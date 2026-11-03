"""足智多谋 · 模型一键下载器（魔搭渠道，断点续传 + 自动重试 + 全程日志）。

用法：python download_models.py（或 .venv\\Scripts\\python.exe download_models.py）
      python download_models.py --with-vision   ← 额外下载视觉模型 qwen2.5vl:7b（约 4.4GB，可选）
产物：model_warehouse\\<模型目录>\\<文件>
日志：gguf\\download_all.log（每次运行追加，含时间戳与进度）

特点：中断后重跑自动续传；单个模型失败不影响其余；全部完成后提示运行安装部署.bat。
"""
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
STAGE = BASE / "gguf"
WH = BASE / "model_warehouse"
LOG = STAGE / "download_all.log"

MODELS = [
    {
        "name": "qwen2.5:7b", "dir": "qwen2.5-7b", "files": [
            ("https://www.modelscope.cn/models/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/master/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf",
             "qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf", 3993201344),
            ("https://www.modelscope.cn/models/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/master/qwen2.5-7b-instruct-q4_k_m-00002-of-00002.gguf",
             "qwen2.5-7b-instruct-q4_k_m-00002-of-00002.gguf", 689872288),
        ],
    },
    {
        "name": "spark-x2.5:4b", "dir": "spark-x2.5-4b", "files": [
            ("https://www.modelscope.cn/models/XHToken/Spark-X2.5-4B-GGUF/resolve/master/Spark-X2.5-4B-Q4_K_M.gguf",
             "Spark-X2.5-4B-Q4_K_M.gguf", 2600224352),
        ],
    },
    {
        "name": "internlm3:8b", "dir": "internlm3-8b", "files": [
            ("https://www.modelscope.cn/models/Shanghai_AI_Laboratory/internlm3-8b-instruct-GGUF/resolve/master/internlm3-8b-instruct-q4_k_m.gguf",
             "internlm3-8b-instruct-q4_k_m.gguf", 5358623936),
        ],
    },
    {
        "name": "qwen2.5-coder-7b:q4_k_m", "dir": "qwen2.5-coder-7b", "files": [
            ("https://www.modelscope.cn/models/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/resolve/master/qwen2.5-coder-7b-instruct-q4_k_m.gguf",
             "qwen2.5-coder-7b-instruct-q4_k_m.gguf", 4683073536),
        ],
    },
    {
        "name": "deepseek-r1:8b", "dir": "deepseek-r1-8b", "files": [
            ("https://www.modelscope.cn/models/bartowski/deepseek-ai_DeepSeek-R1-0528-Qwen3-8B-GGUF/resolve/master/deepseek-ai_DeepSeek-R1-0528-Qwen3-8B-Q4_K_M.gguf",
             "deepseek-ai_DeepSeek-R1-0528-Qwen3-8B-Q4_K_M.gguf", 5027783040),
        ],
    },
    {
        "name": "bge-m3", "dir": "bge-m3", "files": [
            ("https://www.modelscope.cn/models/Xorbits/bge-m3-GGUF/resolve/master/bge-m3-Q8_0.gguf",
             "bge-m3-Q8_0.gguf", 634553856),
        ],
    },
]

# 可选：视觉模型（图片理解，v1.5.0；--with-vision 时才下载）
MODELS_VISION = [
    {
        "name": "qwen2.5vl:7b", "dir": "qwen2.5-vl-7b", "files": [
            ("https://www.modelscope.cn/models/lmstudio-community/Qwen2.5-VL-7B-Instruct-GGUF/resolve/master/Qwen2.5-VL-7B-Instruct-Q4_K_M.gguf",
             "Qwen2.5-VL-7B-Instruct-Q4_K_M.gguf", 4683072032),
            ("https://www.modelscope.cn/models/lmstudio-community/Qwen2.5-VL-7B-Instruct-GGUF/resolve/master/mmproj-model-f16.gguf",
             "mmproj-model-f16.gguf", 1354162912),
        ],
    },
]


def log(msg, echo=True):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    if echo:
        print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def download(url, dest, size):
    cur = dest.stat().st_size if dest.exists() else 0
    if cur >= size:
        return True
    last = time.time()
    while cur < size:
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0", "Range": f"bytes={cur}-"}
            )
            with urllib.request.urlopen(req, timeout=90) as r:
                if r.status == 200 and cur > 0:
                    cur = 0
                    mode = "wb"
                else:
                    mode = "ab"
                with open(dest, mode) as f:
                    while True:
                        chunk = r.read(1 << 20)
                        if not chunk:
                            break
                        f.write(chunk)
                        cur += len(chunk)
                        if time.time() - last >= 30:
                            log(f"  progress {cur * 100.0 / size:.1f}%", echo=False)
                            last = time.time()
        except (urllib.error.URLError, OSError) as e:
            log(f"  retry after error: {e}", echo=False)
            time.sleep(5)
    return cur >= size


def main():
    STAGE.mkdir(exist_ok=True)
    WH.mkdir(exist_ok=True)
    with_vision = "--with-vision" in sys.argv
    models = MODELS + (MODELS_VISION if with_vision else [])
    log(f"=== 足智多谋 模型下载任务开始（共 {len(models)} 个模型{'，含视觉模型' if with_vision else ''}）===")
    done = 0
    for m in models:
        dst = WH / m["dir"]
        dst.mkdir(exist_ok=True)
        ok = True
        for url, fname, size in m["files"]:
            final_path = dst / fname
            if final_path.exists() and final_path.stat().st_size >= size:
                log(f"跳过（已存在）{m['name']} / {fname}")
                continue
            log(f"下载 {m['name']} / {fname}")
            if download(url, STAGE / fname, size):
                os.replace(STAGE / fname, final_path)
                log(f"  完成 {fname}（{size} 字节）")
            else:
                ok = False
                log(f"  失败 {fname}（重跑本脚本可续传）")
        if ok:
            log(f"{m['name']} 已就绪于 model_warehouse\\{m['dir']}")
            done += 1
    log(f"=== 结束：{done}/{len(models)} 个模型就绪 ===")
    if done == len(models):
        log("全部模型就绪。请运行安装部署.bat 完成导入。")
        if with_vision:
            log("视觉模型导入：cd model_warehouse\\qwen2.5-vl-7b 然后 ollama create qwen2.5vl:7b -f Modelfile")
    else:
        log("有模型未完成：重新运行本脚本即可断点续传。")


if __name__ == "__main__":
    main()
