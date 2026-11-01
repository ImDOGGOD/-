"""基础版多 Agent 流水线（分工框架 v2）：固定问题、一次性输出完整结果，适合测试与固定流程。

图结构定义在 core.py，本文件只保留演示入口。
"""
import sys

from core import OLLAMA_URL, build_graph, check_ollama, setup_console


if __name__ == "__main__":
    setup_console()
    if not check_ollama():
        print(f"[!] 无法连接 Ollama 服务（{OLLAMA_URL}）。")
        print("    请先启动 Ollama（桌面应用或命令行 ollama serve），稍等几秒后重试。")
        sys.exit(1)

    question = "用三步说明什么是大语言模型，并给出一个生活中的类比。"
    graph = build_graph()
    result = graph.invoke({"question": question, "revisions": 0, "history": []})

    print("=" * 20, "路径", "=" * 20)
    print(f"mode={result.get('mode')}, revisions={result.get('revisions', 0)}, passed={result.get('passed', True)}")
    print("=" * 20, "规划", "=" * 20)
    print(result.get("plan"))
    print("=" * 20, "最终答案", "=" * 20)
    print(result.get("draft"))
    print("=" * 20, "审查", "=" * 20)
    print(result.get("review"))
