$ErrorActionPreference = "Continue"
$base = "https://www.modelscope.cn/models/bartowski/deepseek-ai_DeepSeek-R1-0528-Qwen3-8B-GGUF/resolve/master"
$outdir = Join-Path $PSScriptRoot "gguf"
$log = Join-Path $outdir "download_r1.log"
New-Item -ItemType Directory -Force -Path $outdir | Out-Null

$name = "deepseek-ai_DeepSeek-R1-0528-Qwen3-8B-Q4_K_M.gguf"
$size = 5027783040
$url = "$base/$name"
$out = Join-Path $outdir $name
$tries = 0
while ($true) {
    $cur = 0
    if (Test-Path -LiteralPath $out) { $cur = (Get-Item -LiteralPath $out).Length }
    if ($cur -ge $size) { break }
    $tries += 1
    "$(Get-Date -Format 'HH:mm:ss') start try=$tries have=$cur" | Out-File -LiteralPath $log -Append -Encoding ascii
    & C:\Windows\System32\curl.exe -sS -L -C - -o "$out" `
        --connect-timeout 15 --speed-time 15 --speed-limit 51200 --max-time 900 "$url"
    "$(Get-Date -Format 'HH:mm:ss') end exit=$LASTEXITCODE" | Out-File -LiteralPath $log -Append -Encoding ascii
    if ($tries -gt 200) { break }
    Start-Sleep -Seconds 2
}
"R1_DONE" | Out-File -LiteralPath $log -Append -Encoding ascii
