"""示例插件：把回答后处理压缩到微博长度（规则截断，演示后处理器机制）。

真正生产级用法可在这里调用任意本地函数/外部 API（如翻译、转格式、
接入平台 API 等——但涉及发布/花钱/控制电脑的操作必须自带白名单与人工确认）。
"""

LIMIT = 140


def _compress(text, limit=LIMIT):
    t = " ".join((text or "").split())
    if len(t) <= limit:
        return t
    return t[: limit - 1] + "…"


POST_PROCESSORS = [
    {"id": "post_compress", "name": "微博压缩", "fn": _compress},
]

PLUGIN_TOOLS = []
