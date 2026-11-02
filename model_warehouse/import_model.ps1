# 模型导入辅助脚本（模型仓库配套）
# 用法：powershell -File 模型仓库\import_model.ps1 -Name "注册名" -Modelfile "模型仓库\子目录\Modelfile"
param(
    [Parameter(Mandatory = $true)][string]$Name,
    [Parameter(Mandatory = $true)][string]$Modelfile
)
$ErrorActionPreference = "Stop"
$mf = Resolve-Path -LiteralPath $Modelfile
Push-Location (Split-Path -Parent $mf.Path)
try {
    Write-Host "正在导入模型 '$Name'（Modelfile: $mf）..."
    ollama create $Name -f $mf.Path
    Write-Host "导入完成。请用 ollama list 核对，并在 models.yaml 中分配岗位。"
} finally {
    Pop-Location
}
