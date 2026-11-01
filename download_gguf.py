from modelscope import snapshot_download

path = snapshot_download(
    "Qwen/Qwen2.5-7B-Instruct-GGUF",
    allow_patterns=["qwen2.5-7b-instruct-q4_k_m-*.gguf"],
    cache_dir="F:/AI/local/models",
)
print(path)
