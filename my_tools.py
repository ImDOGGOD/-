"""自定义工具扩展文件（插件空间）。

把你想加的新功能写成"工具"放在这里，保存后自动生效，无需修改任何其他代码。

规则：
  - 工具 = 一个带 @tool 装饰器的函数；
  - docstring = 给模型的"使用说明书"：写清楚这个工具做什么、什么时候用、参数含义；
  - 函数体 = 实际逻辑；返回值是文本，模型会读取它；
  - 需要外部服务（API key 等）时，把配置写在 models.yaml 新段落里，
    读取方式参照 tools.py 里的 web_search（在函数内部读 yaml）；
  - 危险操作（控制电脑、删除文件、花钱、联网下单）务必加安全限制或人工确认。

扩展思路速查（具体实现留给你研究）：
  1) 图片识别：下载视觉模型到模型仓库（Ollama 支持 llava、qwen2.5vl、moondream 等），
     做一个"读图"工具，把图片路径/base64 发给该视觉模型，返回描述或 OCR 结果；
  2) 识别文件：基于已有 read_file，再做"总结文档"工具（读文件 → 交给模型提炼）；
     PDF/Office 需要先装解析库（pypdf / python-docx / openpyxl）；
  3) 视频创作：本地 8GB 显存跑不了视频生成模型，正确姿势是工具封装外部 API
     （可灵 / 即梦 / Runway 等），key 放 models.yaml 的配置段；
  4) 游戏介入控制：工具封装 pyautogui / pynput（截屏 + 模拟按键），属于高危操作，
     建议动作白名单 + 每次人工确认；游戏画面理解用轻量视觉模型；
  5) 网站聊天：浏览器自动化（selenium / playwright）或直接封装目标网站的 HTTP API。
"""
from langchain_core.tools import tool

# 你新增的工具都要 append 到这个列表，保存后自动生效
TOOLS_EXTRA = []


# ---------------------------------------------------------------
# 示例工具：掷骰子（演示"怎么加一个工具"的最小完整写法）
# ---------------------------------------------------------------
@tool
def dice(sides: int) -> str:
    """掷一个 N 面骰子并返回结果。参数 sides 是骰子面数。"""
    import random

    n = int(sides)
    if not (1 <= n <= 1000000):
        return "面数不合法（应在 1-1000000 之间）"
    return str(random.randint(1, n))


TOOLS_EXTRA.append(dice)

# 想再添加工具时：复制上面这个例子，改函数名 / docstring / 函数体，然后 append 到 TOOLS_EXTRA。
