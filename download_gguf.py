from pathlib import Path

from modelscope import snapshot_download

path = snapshot_download(
    "Qwen/Qwen2.5-7B-Instruct-GGUF",
    allow_patterns=["qwen2.5-7b-instruct-q4_k_m-*.gguf"],
    cache_dir=str(Path(__file__).resolve().parent / "models"),
)
print(path)
