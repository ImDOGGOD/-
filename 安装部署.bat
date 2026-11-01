@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo  ZuZhiDuoMou (Local Multi-Agent System) v1.1.1 - Deploy
echo  Author: DeepSeek (deepseek-v4-pro)
echo ============================================
echo [1/4] Create virtual environment (if missing)...
if not exist ".venv\Scripts\python.exe" python -m venv .venv
if errorlevel 1 (
    echo [!] Failed to create venv. Is Python 3.13 installed and on PATH?
    pause
    exit /b 1
)
echo [2/4] Install dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [!] pip install failed. Check network and retry.
    pause
    exit /b 1
)
echo [3/4] Check Ollama...
where ollama >nul 2>nul
if errorlevel 1 (
    echo [!] ollama not found on PATH. Install Ollama first, run it once, then retry.
    pause
    exit /b 1
)
echo [4/4] Import models from model warehouse...
cd "模型仓库\qwen2.5-7b" && ollama create qwen2.5:7b -f Modelfile
cd "..\spark-x2.5-4b" && ollama create spark-x2.5:4b -f Modelfile
cd "..\internlm3-8b" && ollama create internlm3:8b -f Modelfile
cd "..\qwen2.5-coder-7b" && ollama create qwen2.5-coder-7b:q4_k_m -f Modelfile
cd "..\deepseek-r1-8b" && ollama create deepseek-r1:8b -f Modelfile
cd "..\bge-m3" && ollama create bge-m3 -f Modelfile
cd ..
echo.
echo Deploy finished. Double-click QiDong.bat (start.bat) to use the system.
pause
