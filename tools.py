"""Agent 工具集：计算器、当前时间、文件读取/目录列表、联网搜索（博查，可换）。

安全约定：
- 文件类工具只允许访问 F:\\AI 目录内，单文件不超过 20 万字符；
- 计算器使用 AST 白名单，杜绝任意代码执行；
- 联网搜索的 API key 只存在 models.yaml 的 search 段，可随时更换。
"""
import ast
import datetime
import json
import operator
import os
import urllib.request
from pathlib import Path

from langchain_core.tools import tool

ALLOWED_ROOT = Path(r"F:\AI")
MAX_FILE_CHARS = 200_000

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _calc(node):
    if isinstance(node, ast.Expression):
        return _calc(node.body)
    if isinstance(node, ast.BinOp):
        return _BIN_OPS[type(node.op)](_calc(node.left), _calc(node.right))
    if isinstance(node, ast.UnaryOp):
        return _BIN_OPS[type(node.op)](_calc(node.operand))
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    raise ValueError("unsupported expression")


@tool
def calculator(expression: str) -> str:
    """安全计算数学表达式。输入如 '(3+5)*2' 或 '2**10'（幂用 ** 表示）。"""
    try:
        return str(_calc(ast.parse(expression, mode="eval")))
    except Exception as e:
        return f"计算失败：{e}"


@tool
def current_time() -> str:
    """返回当前日期时间（本地时区）。"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S %A")


def _safe_path(path: str) -> Path:
    # 相对路径以 F:\AI 为基准，便于 Agent 用短路径访问项目文件
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = ALLOWED_ROOT / p
    p = p.resolve()
    if not p.is_relative_to(ALLOWED_ROOT):
        raise ValueError(f"路径超出允许范围（仅限 {ALLOWED_ROOT} 内）")
    return p


@tool
def read_file(path: str) -> str:
    """读取文本文件内容（仅限 F:\\AI 目录内，文件不超过 20 万字符）。"""
    try:
        p = _safe_path(path)
        if not p.is_file():
            return f"文件不存在：{p}"
        if p.stat().st_size > MAX_FILE_CHARS * 4:
            return "文件太大，拒绝读取（超过限制）。"
        return p.read_text(encoding="utf-8", errors="replace")[:MAX_FILE_CHARS]
    except Exception as e:
        return f"读取失败：{e}"


@tool
def list_directory(path: str) -> str:
    """列出目录内容（仅限 F:\\AI 目录内，最多显示 100 项）。"""
    try:
        p = _safe_path(path)
        if not p.is_dir():
            return f"目录不存在：{p}"
        items = sorted(os.listdir(p))[:100]
        lines = [f"{'[D]' if (p / i).is_dir() else '   '} {i}" for i in items]
        return f"共 {len(items)} 项：\n" + "\n".join(lines)
    except Exception as e:
        return f"列出失败：{e}"


def _search_cfg():
    import yaml

    data = yaml.safe_load(Path(__file__).resolve().parent.joinpath("models.yaml").read_text(encoding="utf-8"))
    return data.get("search") or {}


@tool
def web_search(query: str) -> str:
    """联网搜索（博查 API；key 与地址在 models.yaml 的 search 段，可随时更换）。"""
    try:
        c = _search_cfg()
        if not c.get("api_key"):
            return "未配置搜索 API key（models.yaml 的 search.api_key）。"
        body = json.dumps({
            "query": query,
            "freshness": "noLimit",
            "summary": True,
            "count": int(c.get("count", 5)),
        }).encode("utf-8")
        req = urllib.request.Request(
            c.get("base_url", "https://api.bochaai.com/v1/web-search"),
            data=body,
            headers={
                "Authorization": f"Bearer {c['api_key']}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read().decode("utf-8"))
        d = data.get("data") or {}
        pages = (d.get("webPages") or {}).get("value") or []
        lines = []
        for p in pages[: int(c.get("count", 5))]:
            lines.append(f"- {p.get('name')}：{p.get('summary') or p.get('snippet')}（{p.get('url')}）")
        summary = d.get("summary")
        if summary:
            lines.insert(0, f"摘要：{summary}")
        return "\n".join(lines) if lines else f"未找到结果（原始返回前 500 字符：{str(data)[:500]}）"
    except Exception as e:
        return f"搜索失败：{e}"


TOOLS = [calculator, current_time, read_file, list_directory, web_search]


def _load_extra_tools():
    """扩展接口：自动加载同目录的 my_tools.py，把其中的 TOOLS_EXTRA 并入可用工具。"""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "my_tools", str(Path(__file__).resolve().parent / "my_tools.py")
    )
    if spec is None or spec.loader is None:
        return []
    try:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        extra = getattr(mod, "TOOLS_EXTRA", None)
        # @tool 装饰后是 StructuredTool 对象，直接用，不要用 callable() 过滤
        return list(extra or [])
    except Exception as e:
        print(f"[tools] 加载 my_tools.py 失败：{e}")
        return []


TOOLS = TOOLS + _load_extra_tools()
