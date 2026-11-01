"""长期记忆库：SQLite 存储 + 关键词检索 + 模型提炼（分工框架 v2 配套）。

表结构：
    memories(id, ts, kind, content, tags, strength)  —— 长期记忆（手动或自动提炼）
    turns(id, ts, mode, question, answer)            —— 每轮问答存档

聊天命令（chat.py 中以 / 开头，中英文别名均可）：
    /记住 内容   手动存入一条记忆（/remember）
    /回忆 关键词 检索相关记忆与历史问答（/recall）
    /忘记 编号   删除一条记忆（/forget）
    /记忆        查看记忆库统计与最近记忆（/memory）
"""
import re
import sqlite3
import time
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from core import cfg

DB_PATH = Path(__file__).resolve().parent / "memory.db"

DISTILL_PROMPT = (
    "你是记忆提炼助手。从下面的对话中提炼值得长期记住的信息，"
    "例如：用户偏好、用户个人信息、重要事实、结论或待办。"
    "每条一行，最多 3 条；没有值得记住的就只输出“无”。"
    "不要提炼闲聊和一次性的琐碎内容。"
)


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as c:
        c.execute(
            "CREATE TABLE IF NOT EXISTS memories ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, kind TEXT, "
            "content TEXT, tags TEXT, strength INTEGER DEFAULT 1)"
        )
        c.execute(
            "CREATE TABLE IF NOT EXISTS turns ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, mode TEXT, "
            "question TEXT, answer TEXT)"
        )


def _now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def add_memory(content, kind="manual", tags="", strength=1):
    init_db()
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO memories(ts, kind, content, tags, strength) VALUES (?,?,?,?,?)",
            (_now(), kind, content.strip(), tags, strength),
        )
        return cur.lastrowid


def log_turn(mode, question, answer):
    init_db()
    with _conn() as c:
        c.execute(
            "INSERT INTO turns(ts, mode, question, answer) VALUES (?,?,?,?)",
            (_now(), mode, question.strip(), (answer or "")[:2000]),
        )


def delete_memory(mid):
    init_db()
    with _conn() as c:
        cur = c.execute("DELETE FROM memories WHERE id=?", (mid,))
        return cur.rowcount > 0


def stats():
    init_db()
    with _conn() as c:
        n_mem = c.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        n_turn = c.execute("SELECT COUNT(*) FROM turns").fetchone()[0]
        recent = [dict(r) for r in c.execute("SELECT id, ts, kind, content FROM memories ORDER BY id DESC LIMIT 5")]
    return n_mem, n_turn, recent


def _tokens(text):
    """中英文混合分词：英文按词，中文按单字+二元组，用于关键词打分。"""
    t = (text or "").lower()
    words = set(re.findall(r"[a-z0-9]+", t))
    cjk = re.findall(r"[\u4e00-\u9fff]", t)
    return words | {cjk[i] + cjk[i + 1] for i in range(len(cjk) - 1)} | set(cjk)


def _score(query_tokens, text):
    if not query_tokens:
        return 0
    return len(query_tokens & _tokens(text))


def search(query, limit=5):
    """按关键词检索长期记忆，返回带 score 的列表（越相关越靠前）。"""
    init_db()
    q_tokens = _tokens(query)
    with _conn() as c:
        rows = [dict(r) for r in c.execute("SELECT id, ts, kind, content, strength FROM memories")]
    scored = []
    for r in rows:
        s = _score(q_tokens, r["content"])
        if s > 0:
            r["score"] = s * 10 + r["strength"]
            scored.append(r)
    scored.sort(key=lambda r: (-r["score"], -r["id"]))
    return scored[:limit]


def search_turns(query, limit=3):
    """按关键词检索历史问答存档。"""
    init_db()
    q_tokens = _tokens(query)
    with _conn() as c:
        rows = [dict(r) for r in c.execute("SELECT id, ts, mode, question, answer FROM turns ORDER BY id DESC LIMIT 200")]
    scored = []
    for r in rows:
        s = _score(q_tokens, (r["question"] or "") + " " + (r["answer"] or ""))
        if s > 0:
            r["score"] = s
            scored.append(r)
    scored.sort(key=lambda r: (-r["score"], -r["id"]))
    return scored[:limit]


def build_context(query, topk=None):
    """把相关记忆与历史问答拼成一段上下文文本，注入执行者/审查员提示词。"""
    topk = topk or int((cfg.get("memory") or {}).get("topk", 4))
    parts = []
    for m in search(query, limit=topk):
        parts.append(f"- [记忆{m['id']}] {m['content']}")
    for t in search_turns(query, limit=max(1, topk // 2)):
        parts.append(f"- [历史问答{t['id']}] 问：{(t['question'] or '')[:80]} 答：{(t['answer'] or '')[:120]}")
    return "\n".join(parts) if parts else ""


def distill_from_turn(question, answer):
    """用规划师模型从一轮问答中提炼长期记忆条目；失败返回空列表（不影响主流程）。"""
    try:
        c = (cfg.get("general") or {}).get("planner") or {}
        kwargs = {"model": c["model"], "temperature": 0.1}
        if c.get("num_ctx"):
            kwargs["num_ctx"] = int(c["num_ctx"])
        llm = ChatOllama(**kwargs)
        resp = llm.invoke([
            SystemMessage(DISTILL_PROMPT),
            HumanMessage(f"用户问题：{question}\n系统回答：{(answer or '')[:1500]}"),
        ])
        items = []
        for line in (resp.content or "").splitlines():
            line = line.strip().lstrip("-*0123456789.、 ").strip()
            if line and line not in ("无", "没有", "无。", "没有。") and len(line) >= 4:
                items.append(line)
        return items[:3]
    except Exception:
        return []
