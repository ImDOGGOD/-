"""MCP 客户端（v1.7.0）：把 MCP 服务器工具接入 Agent 工具集。

配置（models.yaml 的 mcp 段）：
mcp:
  enabled: true          # 默认 false，接入 MCP 时打开
  servers:
    - name: filesystem
      command: npx
      args: [-y, @modelcontextprotocol/server-filesystem, F:\\AI]
    - name: fetch
      command: uvx
      args: [mcp-server-fetch]
    # 远程服务器（streamable http / sse）：
    # - name: remote
    #   url: http://127.0.0.1:3000/mcp
    #   transport: sse

说明：
    - 每次工具调用新建一次会话（简单可靠，代价是单次调用慢 1-2 秒）；
    - MCP 生态（文件、抓取、数据库、搜索等成百上千现成服务器）经此接入；
    - 服务器不可用时不崩溃：打印原因并跳过。
"""
import asyncio
import json
from pathlib import Path

import yaml

from langchain_core.tools import StructuredTool

BASE = Path(__file__).resolve().parent


def _mcp_cfg():
    try:
        with open(BASE / "models.yaml", "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        return cfg.get("mcp") or {}
    except Exception:
        return {}


def _build_client_config(servers):
    out = {}
    for s in servers or []:
        name = s.get("name")
        if not name:
            continue
        if s.get("url"):
            out[name] = {"url": s["url"], "transport": s.get("transport", "sse")}
        elif s.get("command"):
            out[name] = {"command": s["command"], "args": s.get("args") or []}
    return out


def _client():
    from langchain_mcp_adapters.client import MultiServerMCPClient
    conf = _build_client_config(_mcp_cfg().get("servers"))
    if not conf:
        raise RuntimeError("models.yaml 的 mcp.servers 为空，请先配置")
    return MultiServerMCPClient(conf)


def _fetch_tool_meta():
    """加载全部 MCP 工具元数据（一次性，用于构建包装）。"""
    async def _go():
        async with _client() as client:
            return await client.get_tools()
    return asyncio.run(_go())


def _call_tool(tool_name, input_json):
    """每次调用新建会话执行一次工具，返回文本。"""
    async def _go():
        async with _client() as client:
            tools = await client.get_tools()
            for t in tools:
                if t.name == tool_name:
                    return await t.ainvoke(input_json)
            raise RuntimeError(f"MCP 工具 {tool_name} 不存在（请检查服务器是否在线）")
    return asyncio.run(_go())


def _result_to_text(result):
    content = getattr(result, "content", result)
    if isinstance(content, list):
        parts = []
        for c in content:
            if isinstance(c, dict):
                parts.append(c.get("text") or json.dumps(c, ensure_ascii=False))
            else:
                parts.append(str(c))
        return "\n".join(parts)
    return str(content)


def load_mcp_tools():
    """构建 LangChain 工具包装；未启用/失败时返回 [] 并打印原因。"""
    mcp = _mcp_cfg()
    if not mcp.get("enabled", False):
        return []
    try:
        metas = _fetch_tool_meta()
    except Exception as e:
        print(f"[mcp] 连接失败，跳过 MCP 工具：{e}")
        return []
    tools = []
    for meta in metas:
        name = getattr(meta, "name", "")
        desc = (getattr(meta, "description", "") or "")[:2000]
        if not name:
            continue

        def make_fn(tn):
            def _fn(tool_input: str) -> str:
                try:
                    return _result_to_text(_call_tool(tn, tool_input))
                except Exception as e:
                    return f"[MCP 错误] {e}"
            return _fn

        try:
            tool = StructuredTool.from_function(
                name=name,
                description=desc + "\n\n入参：单个 JSON 字符串，例如 {\"path\": \"F:/AI\"}。",
                func=make_fn(name),
            )
        except Exception as e:
            print(f"[mcp] 工具 {name} 构建失败：{e}")
            continue
        tools.append(tool)
    print(f"[mcp] 已接入 {len(tools)} 个 MCP 工具")
    return tools
