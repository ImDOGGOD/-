$ErrorActionPreference = "Continue"
$base = "https://www.modelscope.cn/models/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/master"
$outdir = "F:\AI\local\gguf"
$log = "F:\AI\local\gguf\download.log"
New-Item -ItemType Directory -Force -Path $outdir | Out-Null

$files = @(
    @{ name = "qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf"; size = 3993201344 },
    @{ name = "qwen2.5-7b-instruct-q4_k_m-00002-of-00002.gguf"; size = 689872288 }
)

foreach ($f in $files) {
    $url = "$base/$($f.name)"
    $out = Join-Path $outdir $f.name
    $tries = 0
    while ($true) {
        $cur = 0
        if (Test-Path -LiteralPath $out) { $cur = (Get-Item -LiteralPath $out).Length }
        if ($cur -ge $f.size) { break }
        $tries += 1
        $stamp = Get-Date -Format "HH:mm:ss"
        "$stamp start $($f.name) try=$tries have=$cur" | Out-File -LiteralPath $log -Append -Encoding ascii
        & C:\Windows\System32\curl.exe -sS -L -C - -o "$out" `
            --connect-timeout 15 --speed-time 15 --speed-limit 51200 --max-time 900 "$url"
        $stamp = Get-Date -Format "HH:mm:ss"
        "$stamp end   $($f.name) exit=$LASTEXITCODE" | Out-File -LiteralPath $log -Append -Encoding ascii
        if ($tries -gt 200) { break }
        Start-Sleep -Seconds 2
    }
}
"ALL_DONE" | Out-File -LiteralPath $log -Append -Encoding ascii
