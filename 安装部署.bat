@echo off
chcp 936 >nul
cd /d "%~dp0"
title 足智多谋 部署工具 v1.1.4
echo ============================================
echo  足智多谋 部署工具  v1.1.4
echo  作者: DeepSeek (deepseek-v4-pro)
echo ============================================
echo.
echo [0/4] 环境自检...
where python >nul 2>nul
if errorlevel 1 goto no_python
python -c "import sys;sys.exit(0 if sys.version_info>=(3,11) else 1)" >nul 2>nul
if errorlevel 1 goto no_python
goto check_ollama
:no_python
echo [!] 未检测到可用的 Python（需要 3.11 及以上，推荐 3.13）。
echo     尝试用 winget 自动安装 Python 3.13 ...
where winget >nul 2>nul
if errorlevel 1 goto no_python_manual
winget install --id Python.Python.3.13 -e --silent --accept-package-agreements --accept-source-agreements
if errorlevel 1 goto no_python_manual
echo [√] Python 3.13 已安装。请【重新双击本脚本】继续部署。
pause
exit /b 0
:no_python_manual
echo [!] 无法自动安装（未找到 winget 或安装失败）。
echo     请手动下载安装 Python 3.13，安装时务必勾选 Add python.exe to PATH：
echo     https://www.python.org/ftp/python/3.13.5/python-3.13.5-amd64.exe
start "" "https://www.python.org/ftp/python/3.13.5/python-3.13.5-amd64.exe"
echo     已为你打开下载页。装好后重新双击本脚本。
pause
exit /b 1
:check_ollama
where ollama >nul 2>nul
if errorlevel 1 goto no_ollama
echo [√] Python 与 Ollama 均已就绪。
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
:no_ollama
where winget >nul 2>nul
if errorlevel 1 goto no_ollama_manual
echo [!] 未检测到 Ollama，尝试用 winget 自动安装 ...
winget install --id Ollama.Ollama -e --silent --accept-package-agreements --accept-source-agreements
if errorlevel 1 goto no_ollama_manual
echo [√] Ollama 已安装。请先从开始菜单运行一次 Ollama（右下角出现图标），
echo     再重新双击本脚本继续。
pause
exit /b 0
:no_ollama_manual
echo [!] 无法自动安装 Ollama。请手动下载安装并运行一次：
echo     https://ollama.com/download/OllamaSetup.exe
start "" "https://ollama.com/download/OllamaSetup.exe"
echo     已为你打开下载页。装好并运行一次后，重新双击本脚本。
pause
exit /b 1