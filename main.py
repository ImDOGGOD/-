"""一键启动入口：自动做环境自检，然后进入交互式多 Agent 系统。

用法：python main.py（或直接双击 启动.bat）
"""
import sys
from pathlib import Path

# 保证无论从哪个目录运行，都能找到同目录下的模块与配置
sys.path.insert(0, str(Path(__file__).resolve().parent))

import chat  # noqa: E402

if __name__ == "__main__":
    chat.main()
