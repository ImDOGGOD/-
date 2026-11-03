"""插件宿主（v1.6.0）：扫描 plugins/ 目录，加载服务端工具与文本后处理器。

插件目录结构：
    plugins/<插件id>/
        manifest.json   插件声明：id/name/version/description（可选 slots）
        plugin.py       服务端：PLUGIN_TOOLS（StructuredTool 列表）、POST_PROCESSORS（后处理器列表）
        plugin.js       前端（可选）：通过 window.ZZDM 挂载按钮/面板等
        config.json     运行时配置（自动生成，如 {"enabled": true}）

安全红线（文档同 plugins/README.md）：
    - 插件是本机信任代码（等同运行任意 Python/JS），只安装你信任的来源；
    - 涉及"控制电脑/删文件/花钱/自动运营社交账号"的插件必须自带白名单与人工确认。
"""
import importlib.util
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
PLUGIN_DIR = BASE / "plugins"


def list_manifests():
    """返回全部 manifest 字典列表（含默认 id）。"""
    out = []
    if not PLUGIN_DIR.is_dir():
        return out
    for d in sorted(PLUGIN_DIR.iterdir()):
        if not d.is_dir():
            continue
        mf = d / "manifest.json"
        if not mf.is_file():
            continue
        try:
            m = json.loads(mf.read_text(encoding="utf-8"))
            m.setdefault("id", d.name)
            out.append(m)
        except Exception:
            continue
    return out


def load_plugins():
    """加载全部插件，返回 (tools, processors)。
    processor 约定：{"id": str, "name": str, "fn": callable(text)->text}"""
    tools, processors = [], []
    if not PLUGIN_DIR.is_dir():
        return tools, processors
    for d in sorted(PLUGIN_DIR.iterdir()):
        py = d / "plugin.py"
        if not py.is_file():
            continue
        try:
            spec = importlib.util.spec_from_file_location(f"zzdm_plugin_{d.name}", py)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)
            for t in getattr(mod, "PLUGIN_TOOLS", []) or []:
                tools.append(t)
            for p in getattr(mod, "POST_PROCESSORS", []) or []:
                if isinstance(p, dict) and callable(p.get("fn")):
                    p.setdefault("id", d.name)
                    p.setdefault("name", d.name)
                    processors.append(p)
        except Exception as e:
            print(f"[plugins] 加载 {d.name} 失败：{e}")
    return tools, processors


def read_config(pid, default=None):
    """读取插件运行时配置（plugins/<id>/config.json）。"""
    if default is None:
        default = {"enabled": True}
    p = PLUGIN_DIR / pid / "config.json"
    if p.is_file():
        try:
            cfg = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(cfg, dict):
                return {**default, **cfg}
        except Exception:
            pass
    return dict(default)


def write_config(pid, updates):
    """合并写入插件运行时配置。"""
    cfg = read_config(pid)
    cfg.update(updates or {})
    d = PLUGIN_DIR / pid
    d.mkdir(parents=True, exist_ok=True)
    (d / "config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    return cfg


def processor_states():
    """当前各后处理器的启用状态（id/name/enabled）。"""
    states = []
    for p in _PROCESSORS:
        cfg = read_config(p.get("id", ""), {"enabled": True})
        states.append({"id": p.get("id"), "name": p.get("name"),
                       "enabled": bool(cfg.get("enabled", True))})
    return states


def apply_postprocess(text):
    """按启用状态依次应用全部后处理器。"""
    for p in _PROCESSORS:
        try:
            cfg = read_config(p.get("id", ""), {"enabled": True})
            if not bool(cfg.get("enabled", True)):
                continue
            out = p["fn"](text)
            if isinstance(out, str):
                text = out
        except Exception as e:
            print(f"[plugins] 后处理 {p.get('id')} 失败：{e}")
    return text


def reload_plugins():
    """重新加载全部插件（拖入新插件文件夹后调用；Web 端有对应按钮）。"""
    global _PLUGIN_TOOLS, _PROCESSORS
    for mod in list(sys.modules):
        if mod.startswith("zzdm_plugin_"):
            del sys.modules[mod]
    _PLUGIN_TOOLS, _PROCESSORS = load_plugins()
    return _PLUGIN_TOOLS, _PROCESSORS


# 启动即加载一次；webui 层直接使用这两个全局
_PLUGIN_TOOLS, _PROCESSORS = load_plugins()
