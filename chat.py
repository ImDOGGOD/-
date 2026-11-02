"""足智多谋 · 交互式多 Agent 系统入口（分工框架 v3：通用问答 / 代码辅助 / Agent 工具 + 长期记忆库）。

运行方式（任选其一）：
  1. 激活虚拟环境后执行 python chat.py
  2. 不激活直接执行 .venv\\Scripts\\python.exe chat.py
  3. 双击 启动.bat

模式与命令：
  直接提问        → 通用问答模式
  /code 问题      → 代码辅助模式（/代码）
  /agent 任务     → Agent 工具模式（/智能体）
  /记住 /回忆 /忘记 /记忆 /帮助 → 长期记忆库命令
"""
from collections import deque

import memory
import kb
from core import (
    OLLAMA_URL,
    __version__,
    ask,
    ask_agent,
    check_ollama,
    cloud_status,
    get_graph,
    get_titles,
    set_cloud_enabled,
    setup_console,
)
from core import cfg

MEM_CFG = cfg.get("memory") or {}


def command_reply(q: str):
    """处理聊天命令，返回回复文本；不是命令时返回 None。终端与 Web 界面共用。"""
    parts = q.split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""
    if cmd in ("/帮助", "/help"):
        return (
            "模式与命令：\n"
            "  直接提问        → 通用问答模式\n"
            "  /code 问题      → 代码辅助模式（/代码）\n"
            "  /agent 任务     → Agent 工具模式（/智能体，可计算/读文件/联网搜索）\n"
            "  /云端 开/关     → 切换云端大模型开关（/cloud）\n"
            "  /记住 内容      → 手动存入长期记忆（/remember）\n"
            "  /回忆 关键词    → 检索记忆与历史问答（/recall）\n"
            "  /忘记 编号      → 删除一条记忆（/forget）\n"
            "  /记忆           → 查看统计与最近记忆（/memory）\n"
            "  /知识 add <文件> | fetch <网址> | 查 <词> | 列表 | 删除 <编号> | 清空（/kb）"
        )
    if cmd in ("/云端", "/cloud"):
        if arg in ("开", "on", "1", "true"):
            st = set_cloud_enabled(True)
            return f"[√] 云端开关已设为：开（密钥{'已配置' if st['configured'] else '未配置，回退本地'}）"
        if arg in ("关", "off", "0", "false"):
            st = set_cloud_enabled(False)
            return "[√] 云端开关已设为：关（全部走本地 Ollama）"
        st = cloud_status()
        return (
            f"云端开关：{'开' if st['enabled'] else '关'}　密钥：{'已配置' if st['configured'] else '未配置（回退本地）'}\n"
            f"服务商：{st['base_url']}　模型：{st['model']}\n用法：/云端 开 | /云端 关"
        )
    if cmd in ("/记住", "/remember"):
        if not arg:
            return "[!] 用法：/记住 想让我长期记住的内容"
        mid = memory.add_memory(arg, kind="manual")
        return f"[√] 已记住（编号 {mid}）：{arg}"
    if cmd in ("/回忆", "/recall"):
        if not arg:
            return "[!] 用法：/回忆 关键词"
        lines = [f"—— 关于“{arg}”的记忆 ——"]
        ms = memory.search(arg, limit=5)
        if ms:
            lines += [f"  [{m['id']}] {m['content']}（{m['ts'][:10]}）" for m in ms]
        else:
            lines.append("  （没有直接相关的长期记忆）")
        ts = memory.search_turns(arg, limit=3)
        if ts:
            lines.append("—— 相关历史问答 ——")
            lines += [f"  [{t['id']}] 问：{(t['question'] or '')[:60]} → 答：{(t['answer'] or '')[:80]}" for t in ts]
        return "\n".join(lines)
    if cmd in ("/忘记", "/forget"):
        if not arg.isdigit():
            return "[!] 用法：/忘记 记忆编号"
        return "[√] 已删除。" if memory.delete_memory(int(arg)) else "[!] 未找到该编号的记忆。"
    if cmd in ("/记忆", "/memory"):
        n_mem, n_turn, recent = memory.stats()
        lines = [f"长期记忆 {n_mem} 条，历史问答 {n_turn} 轮。最近记忆："]
        lines += [f"  [{r['id']}] ({r['kind']}) {r['content']}" for r in recent]
        if n_mem == 0:
            lines.append("  （暂无。用 /记住 内容 手动添加，正常对话后系统也会自动提炼）")
        return "\n".join(lines)
    if cmd in ("/知识", "/kb"):
        sub = arg.split(maxsplit=1)
        act = sub[0].lower()
        rest = sub[1].strip() if len(sub) > 1 else ""
        if act in ("add", "添加", "导入"):
            return "[!] 用法：/知识 add <文件路径>（txt/md）" if not rest else kb.ingest_file(rest)
        if act in ("fetch", "下载"):
            return "[!] 用法：/知识 fetch <网址>" if not rest else kb.ingest_url(rest)
        if act in ("查", "search", "搜索"):
            if not rest:
                return "[!] 用法：/知识 查 <关键词>"
            rs = kb.search(rest, topk=5)
            if not rs:
                return "（知识库为空或无匹配片段）"
            return "\n".join(f"  [{r['id']}] ({r['method']}) {r['text'][:120]}" for r in rs)
        if act in ("列表", "list"):
            n, sources = kb.stats()
            lines = [f"知识片段 {n} 条。最近来源："]
            lines += [f"  - {s['source']}（{s['n']} 段）" for s in sources]
            if n == 0:
                lines.append("  （空。用 /知识 add 文件 或 /知识 fetch 网址 导入）")
            return "\n".join(lines)
        if act in ("删除", "delete"):
            return "[√] 已删除。" if (rest.isdigit() and kb.delete_chunk(int(rest))) else "[!] 用法：/知识 删除 <编号>"
        if act in ("清空", "clear"):
            kb.clear_all()
            return "[√] 知识库已清空。"
        return "[!] 用法：/知识 add <文件> | fetch <网址> | 查 <词> | 列表 | 删除 <编号> | 清空"
    return None


def handle_command(q: str) -> bool:
    rep = command_reply(q)
    if rep is None:
        return False
    print(rep)
    return True


def finish_turn(q, result, mode_label, history):
    """一轮结束后的公共收尾：打印路径、存档、自动提炼记忆。"""
    print("-" * 46)
    print(
        f"路径：{mode_label}　"
        f"修订次数：{result.get('revisions', 0)}，是否通过：{result.get('passed', True)}"
    )
    draft = result.get("draft") or ""
    if draft:
        history.append(f"用户：{q}\n助手：{draft[:600]}")
        memory.log_turn(mode_label, q, draft)
        if MEM_CFG.get("auto_memorize", True) and mode_label in ("complex", "code", "agent"):
            try:
                items = memory.distill_from_turn(q, draft)
                for it in items:
                    memory.add_memory(it, kind="auto")
                if items:
                    print(f"[√] 自动提炼 {len(items)} 条长期记忆（用 /记忆 查看）")
            except Exception:
                pass  # 提炼失败不影响主流程


def main():
    setup_console()
    print(f"足智多谋 v{__version__} 已启动（通用问答 / 代码辅助 / Agent 工具 + 长期记忆库）。")
    print("输入问题开始；/code 代码问题；/agent 任务；/帮助 查看全部命令。")
    if not check_ollama():
        print(f"[!] 无法连接 Ollama 服务（{OLLAMA_URL}）。")
        print("    请先启动 Ollama（桌面应用或命令行 ollama serve），稍等几秒后重试。")
        return
    memory.init_db()
    history = deque(maxlen=4)  # 最近 4 轮对话，供执行者参考（多轮上下文）
    while True:
        try:
            q = input("\n请提问 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见。")
            break
        if not q:
            continue
        if q.lower() in ("quit", "exit", "退出"):
            print("再见。")
            break
        if q.startswith("/"):
            if handle_command(q):
                continue
        mem_ctx = ""
        low = q.lower()
        # 模式分流
        if low.startswith("/code") or low.startswith("/代码"):
            question = q.split(maxsplit=1)[1].strip() if " " in q else ""
            if not question:
                print("[!] 用法：/code 你的编程问题")
                continue
            mem_ctx = memory.build_context(question)
            kb_ctx = kb.build_context(question)
            result = ask(get_graph("code"), get_titles("code"), question, list(history), memory_ctx=mem_ctx, knowledge_ctx=kb_ctx)
            if result is None:
                continue
            finish_turn(question, result, "code", history)
        elif low.startswith("/agent") or low.startswith("/智能体"):
            task = q.split(maxsplit=1)[1].strip() if " " in q else ""
            if not task:
                print("[!] 用法：/agent 你的任务")
                continue
            mem_ctx = memory.build_context(task)
            kb_ctx = kb.build_context(task)
            result = ask_agent(task, memory_ctx=mem_ctx, knowledge_ctx=kb_ctx)
            if result is None:
                continue
            msgs = result.get("messages") or []
            answer = ""
            for m in reversed(msgs):
                if getattr(m, "content", None):
                    answer = m.content
                    break
            print("-" * 46)
            print(f"路径：agent　是否通过：{result.get('passed', True)}")
            if answer:
                history.append(f"用户：{task}\n助手：{answer[:600]}")
                memory.log_turn("agent", task, answer)
                if MEM_CFG.get("auto_memorize", True):
                    try:
                        items = memory.distill_from_turn(task, answer)
                        for it in items:
                            memory.add_memory(it, kind="auto")
                        if items:
                            print(f"[√] 自动提炼 {len(items)} 条长期记忆（用 /记忆 查看）")
                    except Exception:
                        pass
        else:
            mem_ctx = memory.build_context(q)
            kb_ctx = kb.build_context(q)
            result = ask(get_graph("general"), get_titles("general"), q, list(history), memory_ctx=mem_ctx, knowledge_ctx=kb_ctx)
            if result is None:
                continue
            finish_turn(q, result, result.get("mode", "?"), history)


if __name__ == "__main__":
    main()
