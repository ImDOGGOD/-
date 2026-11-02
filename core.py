"""分工框架 v3 核心：三模式分离 + 团队身份 + 记忆注入。

模式一 通用问答（general）：规划 → 执行 → 审查 闭环（元问题直达、简单问题快答）
模式二 代码辅助（code）：同结构，使用代码专用提示词与模型（可换 Coder 特化模型）
模式三 Agent（agent）：工具调用循环（执行模型）+ 审查回路（双模型协作）

多轮上下文与长期记忆由调用方通过 history / memory_ctx 传入。
"""
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Annotated, TypedDict

import yaml

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages

BASE_DIR = Path(__file__).resolve().parent
OLLAMA_URL = "http://127.0.0.1:11434"

__version__ = "1.3.0"
__author__ = "谋士 (MoShi)"

# 元问题关键词（中英文，规则预判，零成本直达编排层）
META_KEYWORDS = [
    "你是谁", "你们是谁", "你是谁啊",
    "介绍你们自己", "介绍你自己", "自我介绍",
    "你叫什么名字", "你们叫什么", "你叫什么",
    "你是什么系统", "你是什么模型", "你们是什么",
    "团队里有哪些", "团队成员", "哪些模型", "有几个模型", "什么模型",
    "你怎么工作", "你们怎么工作", "工作流程", "系统怎么工作", "系统介绍", "系统架构",
    "whoareyou", "introduceyourself", "introduceyourselves",
    "whatareyou", "whatmodel", "yourteam", "tellmeaboutyourself",
]


def setup_console() -> None:
    """让 Windows 控制台按 UTF-8 输出，避免特殊字符触发 UnicodeEncodeError。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def check_ollama(timeout: float = 3.0) -> bool:
    """检查 Ollama 服务是否可用。"""
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/version", timeout=timeout) as resp:
            return resp.status == 200
    except (urllib.error.URLError, OSError):
        return False


with open(BASE_DIR / "models.yaml", "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)


def _section(section):
    return cfg.get(section) or {}


def _role(section, role_key):
    return _section(section).get(role_key) or {}


def _cloud_section():
    return cfg.get("cloud") or {}


# 云端运行时开关：初始值取 models.yaml，客户端可通过 set_cloud_enabled 动态切换
CLOUD_STATE = {"enabled": bool(_cloud_section().get("enabled", False))}


def _make_llm(section, role_key):
    c = _role(section, role_key)
    cloud = _cloud_section()
    use_cloud = (
        CLOUD_STATE["enabled"]
        and role_key in (cloud.get("roles") or [])
        and bool(cloud.get("api_key"))
        and bool(cloud.get("base_url"))
    )
    if use_cloud:
        # 兼容 OpenAI 接口的云端大模型（DeepSeek/通义/智谱/OpenAI 等）
        kwargs = {
            "model": cloud.get("model") or c.get("model"),
            "api_key": cloud.get("api_key"),
            "base_url": cloud.get("base_url"),
            "temperature": c.get("temperature", cloud.get("temperature", 0.3)),
        }
        max_tokens = cloud.get("num_predict") or c.get("num_predict")
        if max_tokens:
            kwargs["max_tokens"] = int(max_tokens)
        return ChatOpenAI(**kwargs), c.get("role", "")
    # 本地 Ollama 模型（默认；云端未配置 key 时也自动回退到此）
    kwargs = {"model": c.get("model"), "temperature": c.get("temperature", 0.3)}
    if c.get("num_ctx"):
        kwargs["num_ctx"] = int(c["num_ctx"])
    if c.get("num_predict"):
        kwargs["num_predict"] = int(c["num_predict"])
    return ChatOllama(**kwargs), c.get("role", "")


def build_team_intro() -> str:
    """按 models.yaml 动态生成团队介绍，换模型后自动同步。"""
    general = _section("general")
    p = _role("general", "planner").get("model", "?")
    e = _role("general", "executor").get("model", "?")
    r = _role("general", "reviewer").get("model", "?")
    max_rev = general.get("max_revisions", 2)
    return (
        "我是“足智多谋”——一套本地多智能体系统——的编排层（LangGraph 状态图），团队共有三位模型成员，"
        "全部在你电脑本地运行：\n\n"
        f"1. 规划师 —— {p}：负责把问题分类（元问题/简单/复杂）并拆解成执行步骤；\n"
        f"2. 执行者 —— {e}：负责按计划产出完整答案；\n"
        f"3. 审查员 —— {r}：负责交叉检查答案，不合格会退回重做（最多修订 {max_rev} 次）。\n\n"
        "工作流程：每个问题先由规划师分类——关于我们自身的问题由编排层直接回答；简单问题快速直答；"
        "复杂问题走“规划 → 执行 → 审查”闭环。\n\n"
        "系统共三种模式：直接提问=通用问答；/code 问题=代码辅助；/agent 任务=Agent 工具模式（可计算、"
        "读文件、联网搜索）。\n\n"
        "关于我：我是负责协调的编排程序，不联网、数据不出本机；具备本轮对话内的多轮上下文和长期记忆库。"
    )


TEAM_INTRO = build_team_intro()


class PipelineState(TypedDict, total=False):
    question: str
    mode: str          # meta / simple / complex
    plan: str
    draft: str
    review: str
    passed: bool
    revisions: int
    history: list      # 最近几轮对话（调用方传入，本轮不追加）
    memory_ctx: str    # 长期记忆检索片段（调用方传入）
    knowledge_ctx: str  # 知识库检索片段（调用方传入）


def rule_meta(question: str) -> bool:
    """规则预判元问题（关于系统自身），避免把“介绍你们自己”送进规划师。"""
    q = (question or "").lower().replace(" ", "")
    return any(k in q for k in META_KEYWORDS)


def parse_mode(text: str) -> str:
    """从规划师输出中解析问题类型；解析失败默认走复杂路径（保质量）。"""
    t = (text or "").upper().replace(" ", "")
    if "SIMPLE" in t or "简单" in t:
        return "simple"
    return "complex"


def extract_plan(text: str) -> str:
    """从规划师输出中抽取计划部分。"""
    t = (text or "").strip()
    for sep in ("计划：", "计划:", "计划 :"):
        if sep in t:
            return t.split(sep, 1)[1].strip()
    return t


def make_router_node(planner_llm, planner_role):
    def router_node(state: PipelineState):
        question = state["question"]
        if rule_meta(question):
            return {"mode": "meta", "plan": ""}
        resp = planner_llm.invoke([
            SystemMessage(planner_role),
            HumanMessage(f"问题：{question}\n请按格式输出类型和计划。"),
        ])
        text = resp.content or ""
        return {"mode": parse_mode(text), "plan": extract_plan(text)}
    return router_node


def make_executor_node(executor_llm, executor_role):
    def executor_node(state: PipelineState):
        mode = state.get("mode") or "complex"
        parts = []
        if state.get("history"):
            hist = "\n".join(str(h) for h in state["history"][-6:])
            parts.append(f"最近的对话历史（供上下文参考，不要重复回答历史问题）：\n{hist}")
        if state.get("memory_ctx"):
            parts.append(f"长期记忆（系统记住的与用户相关的过往信息，可能相关，仅供参考）：\n{state['memory_ctx']}")
        if state.get("knowledge_ctx"):
            parts.append(f"知识库资料（检索到的参考内容，回答时优先采信其中信息）：\n{state['knowledge_ctx']}")
        parts.append(f"用户问题：{state['question']}")
        if mode == "simple":
            parts.append("（这是简单问题，请直接给出简洁准确的回答，不要展开。）")
        else:
            parts.append(f"执行计划：{state.get('plan') or '（无计划，请自行组织回答）'}")
            if state.get("review"):
                parts.append(f"上一版审查意见，请据此修正：{state['review']}")
        resp = executor_llm.invoke([
            SystemMessage(executor_role),
            HumanMessage("\n".join(parts)),
        ])
        return {"draft": resp.content, "revisions": state.get("revisions", 0) + 1}
    return executor_node


def judge_passed(text: str) -> bool:
    """解析审查结论：取最后一条“判定：通过/退回”；没有显式判定时按否定词与“通过”兜底。"""
    if not text:
        return False
    t = text.replace(" ", "")
    verdicts = re.findall(r"判定[::：]\s*(通过|退回)", t)
    if verdicts:
        return verdicts[-1] == "通过"
    if "未通过" in t or "不通过" in t or "未达标" in t or "不合格" in t:
        return False
    return "通过" in t


def make_reviewer_node(reviewer_llm, reviewer_role):
    def reviewer_node(state: PipelineState):
        instruction = f"用户问题：{state['question']}\n待审查答案：{state['draft']}\n"
        if state.get("memory_ctx"):
            instruction += f"相关长期记忆（供核对事实参考）：{state['memory_ctx']}\n"
        if state.get("knowledge_ctx"):
            instruction += f"知识库参考资料（供核对事实参考）：{state['knowledge_ctx']}\n"
        instruction += "请指出问题；若答案合格，在最后一行写“判定：通过”，否则写“判定：退回”。"
        resp = reviewer_llm.invoke([
            SystemMessage(reviewer_role),
            HumanMessage(instruction),
        ])
        return {"review": resp.content, "passed": judge_passed(resp.content)}
    return reviewer_node


def meta_answer_node(state: PipelineState):
    """元问题：由编排层直接回答，无需任何模型。"""
    return {
        "plan": "（关于系统自身的问题，由编排层直接回答）",
        "draft": TEAM_INTRO,
        "passed": True,
    }


def finalize_node(state: PipelineState):
    """简单问题收尾：直答即通过。"""
    return {"passed": True}


def route_after_router(state: PipelineState):
    return state.get("mode") or "complex"


def route_after_executor(state: PipelineState):
    return "simple" if state.get("mode") == "simple" else "complex"


def build_pipeline(section: str):
    """按配置段构建“规划 → 执行 → 审查”闭环图。"""
    planner_llm, planner_role = _make_llm(section, "planner")
    executor_llm, executor_role = _make_llm(section, "executor")
    reviewer_llm, reviewer_role = _make_llm(section, "reviewer")
    max_rev = int(_section(section).get("max_revisions", 2))

    def route_after_review(state):
        if state.get("passed") or state.get("revisions", 0) >= max_rev:
            return "finish"
        return "revise"

    builder = StateGraph(PipelineState)
    builder.add_node("router", make_router_node(planner_llm, planner_role))
    builder.add_node("executor", make_executor_node(executor_llm, executor_role))
    builder.add_node("reviewer", make_reviewer_node(reviewer_llm, reviewer_role))
    builder.add_node("meta_answer", meta_answer_node)
    builder.add_node("finalize", finalize_node)
    builder.add_edge(START, "router")
    builder.add_conditional_edges(
        "router", route_after_router,
        {"meta": "meta_answer", "simple": "executor", "complex": "executor"},
    )
    builder.add_edge("meta_answer", END)
    builder.add_conditional_edges(
        "executor", route_after_executor,
        {"simple": "finalize", "complex": "reviewer"},
    )
    builder.add_edge("finalize", END)
    builder.add_conditional_edges(
        "reviewer", route_after_review,
        {"finish": END, "revise": "executor"},
    )
    return builder.compile()


def make_titles(section: str):
    cloud = _cloud_section()

    def label(role_key):
        local_model = _role(section, role_key).get("model", "?")
        on_cloud = (
            CLOUD_STATE["enabled"]
            and role_key in (cloud.get("roles") or [])
            and cloud.get("api_key")
            and cloud.get("base_url")
        )
        if on_cloud:
            return f"{cloud.get('model') or local_model}（云端）"
        return local_model

    return {
        "router": f"路由/规划 {label('planner')}",
        "executor": f"执行 {label('executor')}",
        "reviewer": f"审查 {label('reviewer')}",
        "meta_answer": "系统自我介绍",
    }


GENERAL_GRAPH = build_pipeline("general")
CODE_GRAPH = build_pipeline("code")
GENERAL_TITLES = make_titles("general")
CODE_TITLES = make_titles("code")


def build_graph():
    """兼容旧入口：返回通用问答图。"""
    return GENERAL_GRAPH


def iter_ask(graph_obj, titles, question, history=None, memory_ctx=None, knowledge_ctx=None):
    """流式执行一次提问，逐个产出事件：
    ("banner", 标题) 角色切换 / ("text", 文本) 增量输出 / ("final", 最终状态) / ("error", 消息)。
    控制台与 Web 界面共用本生成器。"""
    last_node = None
    final = None
    try:
        for mode, payload in graph_obj.stream(
            {
                "question": question,
                "revisions": 0,
                "history": list(history or []),
                "memory_ctx": memory_ctx or "",
                "knowledge_ctx": knowledge_ctx or "",
            },
            stream_mode=["messages", "values"],
        ):
            if mode == "messages":
                chunk, chunk_meta = payload
                node = chunk_meta.get("langgraph_node")
                if node != last_node:
                    yield ("banner", titles.get(node, node))
                    last_node = node
                if chunk.content:
                    yield ("text", chunk.content)
            elif mode == "values":
                final = payload
    except Exception as exc:
        yield ("error", f"{exc.__class__.__name__}: {exc}")
        return
    if final and final.get("mode") == "meta":
        # meta_answer 节点没有模型流式输出，无论路由是否产生过文本都补发团队介绍
        yield ("banner", titles.get("meta_answer", "系统自我介绍"))
        yield ("text", final.get("draft", ""))
    yield ("final", final)


def ask(graph_obj, titles, question, history=None, memory_ctx=None, knowledge_ctx=None):
    """控制台版：消费 iter_ask 事件并打印；返回最终状态（出错返回 None）。"""
    final = None
    first = True
    for ev, data in iter_ask(graph_obj, titles, question, history, memory_ctx, knowledge_ctx):
        if ev == "banner":
            if not first:
                print()
            print("\n" + "=" * 14 + " " + data + " " + "=" * 14)
            first = False
        elif ev == "text":
            print(data, end="", flush=True)
        elif ev == "error":
            print()
            print(f"[!] 运行出错：{data}")
            print("    常见原因：Ollama 服务未启动、模型未导入（用 ollama list 检查）、显存不足。")
            return None
        elif ev == "final":
            final = data
    print()
    return final


# ---------------- Agent 模式（工具调用循环 + 审查回路，双模型协作） ----------------

class AgentRuntimeState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    question: str
    memory_ctx: str
    review: str
    passed: bool
    revisions: int
    tool_steps: int


def build_agent_graph():
    import tools  # 延迟导入，避免循环依赖

    from langgraph.prebuilt import ToolNode

    sec = _section("agent")
    agent_llm_base, agent_role = _make_llm("agent", "executor")
    reviewer_llm, reviewer_role = _make_llm("agent", "reviewer")
    max_rev = int(sec.get("max_revisions", 2))
    max_steps = int(sec.get("max_tool_steps", 10))
    agent_llm = agent_llm_base.bind_tools(tools.TOOLS)

    def agent_node(state):
        msgs = list(state.get("messages") or [])
        if state.get("review"):
            msgs = msgs + [HumanMessage("上一轮审查意见，请据此修正并重新完成任务：\n" + state["review"])]
        resp = agent_llm.invoke(msgs)
        return {"messages": [resp]}

    def tools_node(state):
        msgs = list(state.get("messages") or [])
        # 防御：小模型可能一次生成大量重复工具调用，只执行第一个，其余丢弃
        if msgs and getattr(msgs[-1], "tool_calls", None) and len(msgs[-1].tool_calls) > 1:
            trimmed = msgs[-1].copy(update={"tool_calls": msgs[-1].tool_calls[:1]})
            msgs = msgs[:-1] + [trimmed]
        out = ToolNode(tools.TOOLS).invoke({"messages": msgs})
        return {**out, "tool_steps": state.get("tool_steps", 0) + 1}

    def reviewer_node(state):
        msgs = state.get("messages") or []
        answer = ""
        tool_log = []
        for m in msgs:
            for tc in getattr(m, "tool_calls", None) or []:
                tool_log.append(tc.get("name", "?"))
            if isinstance(m, AIMessage) and m.content:
                answer = m.content
        tool_info = f"Agent 调用过的工具：{', '.join(tool_log)}" if tool_log else "Agent 未调用任何工具"
        instruction = (
            f"任务：{state['question']}\n{tool_info}\nAgent 的最终回答：{answer}\n"
            "请检查任务是否真正完成、结果是否正确、是否有遗漏；最后一行写“判定：通过”或“判定：退回”。"
        )
        resp = reviewer_llm.invoke([SystemMessage(reviewer_role), HumanMessage(instruction)])
        return {"review": resp.content, "passed": judge_passed(resp.content)}

    def feedback_node(state):
        return {"revisions": state.get("revisions", 0) + 1}

    def route_agent(state):
        msgs = state.get("messages") or []
        if msgs and getattr(msgs[-1], "tool_calls", None):
            return "tools"
        return "reviewer"

    def route_after_tools(state):
        if state.get("tool_steps", 0) >= max_steps:
            return "reviewer"
        return "agent"

    def route_after_review(state):
        if state.get("passed") or state.get("revisions", 0) >= max_rev:
            return "finish"
        return "feedback"

    builder = StateGraph(AgentRuntimeState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", tools_node)
    builder.add_node("reviewer", reviewer_node)
    builder.add_node("feedback", feedback_node)
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", route_agent, {"tools": "tools", "reviewer": "reviewer"})
    builder.add_conditional_edges("tools", route_after_tools, {"agent": "agent", "reviewer": "reviewer"})
    builder.add_conditional_edges("reviewer", route_after_review, {"finish": END, "feedback": "feedback"})
    builder.add_edge("feedback", "agent")
    return builder.compile()


AGENT_GRAPH = build_agent_graph()


def make_agent_titles():
    cloud = _cloud_section()

    def label(role_key):
        local_model = _role("agent", role_key).get("model", "?")
        on_cloud = (
            CLOUD_STATE["enabled"]
            and role_key in (cloud.get("roles") or [])
            and cloud.get("api_key")
            and cloud.get("base_url")
        )
        if on_cloud:
            return f"{cloud.get('model') or local_model}（云端）"
        return local_model

    return {
        "agent": f"Agent 执行 {label('executor')}",
        "tools": "工具调用",
        "reviewer": f"Agent 审查 {label('reviewer')}",
        "feedback": "退回重做",
    }


AGENT_TITLES = make_agent_titles()


def iter_agent(question, memory_ctx=None, knowledge_ctx=None):
    """流式执行 Agent 模式：事件同 iter_ask，另有 ("tool", "名称 参数") 事件。"""
    last_node = None
    final = None
    try:
        _, agent_role = _make_llm("agent", "executor")
        prefix = f"任务：{question}"
        if memory_ctx:
            prefix += f"\n相关长期记忆：{memory_ctx}"
        if knowledge_ctx:
            prefix += f"\n知识库资料：{knowledge_ctx}"
        for mode, payload in AGENT_GRAPH.stream(
            {
                "messages": [SystemMessage(agent_role), HumanMessage(prefix)],
                "question": question,
                "memory_ctx": memory_ctx or "",
            },
            stream_mode=["messages", "values"],
        ):
            if mode == "messages":
                chunk, chunk_meta = payload
                node = chunk_meta.get("langgraph_node")
                if node != last_node:
                    yield ("banner", AGENT_TITLES.get(node, node))
                    last_node = node
                if getattr(chunk, "tool_call_chunks", None):
                    for tc in chunk.tool_call_chunks:
                        if tc.get("name"):
                            yield ("tool", f"{tc['name']} {tc.get('args', '')}")
                elif chunk.content:
                    yield ("text", chunk.content)
            elif mode == "values":
                final = payload
    except Exception as exc:
        yield ("error", f"{exc.__class__.__name__}: {exc}")
        return
    yield ("final", final)


def ask_agent(question, memory_ctx=None, knowledge_ctx=None):
    """控制台版 Agent 模式（工具循环 + 审查回路）；返回最终状态（出错返回 None）。"""
    final = None
    first = True
    for ev, data in iter_agent(question, memory_ctx, knowledge_ctx):
        if ev == "banner":
            if not first:
                print()
            print("\n" + "=" * 14 + " " + data + " " + "=" * 14)
            first = False
        elif ev == "text":
            print(data, end="", flush=True)
        elif ev == "tool":
            print(f"\n[调用工具 {data}]", end="")
        elif ev == "error":
            print()
            print(f"[!] Agent 运行出错：{data}")
            return None
        elif ev == "final":
            final = data
    print()
    return final


# ---------------- 云端混合模式：运行时开关与图管理 ----------------

def _rebuild_graphs():
    """按当前 CLOUD_STATE 重新构建全部图与标题，替换模块级实例。"""
    global GENERAL_GRAPH, CODE_GRAPH, AGENT_GRAPH
    global GENERAL_TITLES, CODE_TITLES, AGENT_TITLES
    GENERAL_GRAPH = build_pipeline("general")
    CODE_GRAPH = build_pipeline("code")
    AGENT_GRAPH = build_agent_graph()
    GENERAL_TITLES = make_titles("general")
    CODE_TITLES = make_titles("code")
    AGENT_TITLES = make_agent_titles()


def set_cloud_enabled(flag):
    """切换云端开关并重建图（每次都重建，保证图与当前配置/roles一致）。返回最新状态。"""
    flag = bool(flag)
    CLOUD_STATE["enabled"] = flag
    _rebuild_graphs()
    return cloud_status()


def cloud_status():
    cloud = _cloud_section()
    return {
        "enabled": CLOUD_STATE["enabled"],
        "configured": bool(cloud.get("api_key")),
        "provider": cloud.get("provider", ""),
        "base_url": cloud.get("base_url", ""),
        "model": cloud.get("model", ""),
        "roles": list(cloud.get("roles") or []),
    }


def get_graph(mode):
    """前端统一入口：返回当前（重建后的）图实例。"""
    return {"general": GENERAL_GRAPH, "code": CODE_GRAPH, "agent": AGENT_GRAPH}[mode]


def get_titles(mode):
    """前端统一入口：返回当前（重建后的）标题。"""
    return {"general": GENERAL_TITLES, "code": CODE_TITLES, "agent": AGENT_TITLES}[mode]
