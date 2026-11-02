"""下载 bge-m3-Q8_0.gguf（魔搭 Xorbits 仓库，断点续传 + 自动重试）。"""
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

URL = "https://www.modelscope.cn/models/Xorbits/bge-m3-GGUF/resolve/master/bge-m3-Q8_0.gguf"
_GGUF_DIR = Path(__file__).resolve().parent / "gguf"
OUT = str(_GGUF_DIR / "bge-m3-Q8_0.gguf")
LOG = str(_GGUF_DIR / "download_bge.log")
SIZE = 634553856

os.makedirs(os.path.dirname(OUT), exist_ok=True)


def log(msg):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


cur = os.path.getsize(OUT) if os.path.exists(OUT) else 0
log(f"start have={cur} size={SIZE}")
last = time.time()
while cur < SIZE:
    try:
        req = urllib.request.Request(
            URL, headers={"User-Agent": "Mozilla/5.0", "Range": f"bytes={cur}-"}
        )
        with urllib.request.urlopen(req, timeout=90) as r:
            if r.status == 200 and cur > 0:
                log("server ignored Range, restarting from 0")
                cur = 0
                mode = "wb"
            else:
                mode = "ab"
            with open(OUT, mode) as f:
                while True:
                    chunk = r.read(1 << 20)
                    if not chunk:
                        break
                    f.write(chunk)
                    cur += len(chunk)
                    if time.time() - last >= 30:
                        log(f"progress {cur * 100.0 / SIZE:.1f}% have={cur}")
                        last = time.time()
    except (urllib.error.URLError, OSError) as e:
        log(f"retry after error: {e}")
        time.sleep(5)
log("BGE_DONE")
