@echo off
chcp 936 >nul
cd /d "%~dp0"
title 足智多谋 部署工具 v1.1.3
echo ============================================
echo  足智多谋 部署工具  v1.1.3
echo  作者: DeepSeek (deepseek-v4-pro)
echo ============================================
echo [1/4] 创建虚拟环境（如不存在）...
if not exist ".venv\Scripts\python.exe" python -m venv .venv
if errorlevel 1 (
    echo [!] 创建虚拟环境失败，请确认已安装 Python 3.13 并加入 PATH
    pause
    exit /b 1
)
echo [2/4] 安装依赖...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [!] 依赖安装失败，请检查网络后重试
    pause
    exit /b 1
)
echo [3/4] 检查 Ollama...
where ollama >nul 2>nul
if errorlevel 1 (
    echo [!] 未找到 ollama，请先安装 Ollama 并运行一次
    pause
    exit /b 1
)
echo [4/4] 从模型仓库导入六个模型...
cd "模型仓库\qwen2.5-7b" && ollama create qwen2.5:7b -f Modelfile
cd "..\spark-x2.5-4b" && ollama create spark-x2.5:4b -f Modelfile
cd "..\internlm3-8b" && ollama create internlm3:8b -f Modelfile
cd "..\qwen2.5-coder-7b" && ollama create qwen2.5-coder-7b:q4_k_m -f Modelfile
cd "..\deepseek-r1-8b" && ollama create deepseek-r1:8b -f Modelfile
cd "..\bge-m3" && ollama create bge-m3 -f Modelfile
cd ..
echo.
echo 部署完成！双击 启动.bat，选 [1] Web 界面 或 [2] 终端版。
pause