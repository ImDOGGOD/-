@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title ZuZhiDuoMou Deploy v2.1.3
echo ============================================
echo   ZuZhiDuoMou  Deploy Tool  v2.1.3
echo   Author: MoShi
echo ============================================
echo.
echo [0/6] Checking environment...
where python >nul 2>nul
if errorlevel 1 goto no_python
python -c "import sys;sys.exit(0 if sys.version_info>=(3,11) else 1)" >nul 2>nul
if errorlevel 1 goto no_python
goto check_ollama
:no_python
echo [WARN] Python 3.11+ (3.13 recommended) not found.
echo     Trying to install Python 3.13 with winget ...
where winget >nul 2>nul
if errorlevel 1 goto no_python_manual
winget install --id Python.Python.3.13 -e --silent --accept-package-agreements --accept-source-agreements
if errorlevel 1 goto no_python_manual
echo [OK] Python 3.13 installed. Please double-click this script again.
pause
exit /b 0
:no_python_manual
echo [WARN] Auto-install failed (no winget or install error).
echo     Download and install Python 3.13 manually
echo     (check "Add python.exe to PATH" during install):
echo     https://www.python.org/ftp/python/3.13.5/python-3.13.5-amd64.exe
start "" "https://www.python.org/ftp/python/3.13.5/python-3.13.5-amd64.exe"
echo     Download page opened. Re-run this script after installing.
pause
exit /b 1
:check_ollama
where ollama >nul 2>nul
if errorlevel 1 goto no_ollama
echo [OK] Python and Ollama are ready.
echo [1/6] Creating virtual environment (if missing)...
if not exist ".venv\Scripts\python.exe" python -m venv .venv
if errorlevel 1 (
    echo [WARN] Failed to create venv. Check Python installation and PATH.
    pause
    exit /b 1
)
echo [2/6] Installing dependencies (PyPI official source)...
if not exist "models.yaml" copy "models.yaml.example" "models.yaml" >nul
".venv\Scripts\python.exe" -m pip install -r requirements.txt -i https://pypi.org/simple/ --timeout 60 --retries 3
if not errorlevel 1 goto deps_ok
echo [WARN] Official source failed. Retrying with default source...
".venv\Scripts\python.exe" -m pip install -r requirements.txt --timeout 60 --retries 3
if not errorlevel 1 goto deps_ok
echo [ERROR] pip install failed. Possible causes:
echo    1. Network blocked / DNS / firewall
echo    2. pip mirror misconfigured - try deleting C:\Users\YOU\pip\pip.ini
echo    3. 32-bit Python - some packages need 64-bit Python
echo    Screenshot the error above and send to developer.
pause
exit /b 1
:deps_ok
echo [3/6] Verifying feature dependencies...
".venv\Scripts\python.exe" -c "import pypdf,docx,openpyxl,langchain_mcp_adapters" >nul 2>nul
if errorlevel 1 (
    echo     Retrying missing file/MCP libraries...
    ".venv\Scripts\python.exe" -m pip install pypdf python-docx openpyxl langchain-mcp-adapters -i https://pypi.org/simple/
)
".venv\Scripts\python.exe" -c "import pypdf,docx,openpyxl,langchain_mcp_adapters;print('  OK  file + MCP libraries')" 2>nul
if errorlevel 1 echo [WARN] Optional libraries missing - file/MCP features may be limited.
echo.
echo [5/6] Checking toolchain dependencies...
where nvidia-smi >nul 2>nul
if errorlevel 1 (
    echo [WARN] nvidia-smi not found. GPU monitoring will not work.
    echo     Please install NVIDIA driver from: https://www.nvidia.com/Download/index.aspx
) else (
    echo [OK] nvidia-smi found.
)
where node >nul 2>nul
if errorlevel 1 (
    echo [WARN] Node.js not found. Some MCP servers require Node.js.
    where winget >nul 2>nul
    if not errorlevel 1 (
        echo     Installing Node.js via winget...
        winget install --id OpenJS.NodeJS.LTS -e --silent --accept-package-agreements --accept-source-agreements
        if not errorlevel 1 echo [OK] Node.js installed.
    ) else (
        echo     Please install Node.js manually from: https://nodejs.org/
    )
) else (
    echo [OK] Node.js found.
)
where npx >nul 2>nul
if errorlevel 1 (
    echo [WARN] npx not found. Some MCP servers require npx.
    where winget >nul 2>nul
    if not errorlevel 1 (
        echo     Installing npx via winget (bundled with Node.js)...
        winget install --id OpenJS.NodeJS.LTS -e --silent --accept-package-agreements --accept-source-agreements
    ) else (
        echo     Please install Node.js (includes npx) from: https://nodejs.org/
    )
) else (
    echo [OK] npx found.
)
where uvx >nul 2>nul
if errorlevel 1 (
    echo [WARN] uvx not found. Some MCP servers require uvx.
    where winget >nul 2>nul
    if not errorlevel 1 (
        echo     Installing uv via winget...
        winget install --id Astral.uv -e --silent --accept-package-agreements --accept-source-agreements
        if not errorlevel 1 echo [OK] uvx installed.
    ) else (
        echo     Please install uv manually: pip install uv
    )
) else (
    echo [OK] uvx found.
)
echo.
echo [5/6] Checking model files...
if not exist "model_warehouse\qwen2.5-7b\qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf" (
    echo [WARN] Model files not found in model_warehouse.
    set /p DL=Download all 6 core models now (about 13 GB)? [Y/N]: 
    if /i "!DL!"=="Y" (
        echo     Downloading... this takes a while. Log: gguf\download_all.log
        ".venv\Scripts\python.exe" download_models.py
        if errorlevel 1 (
            echo [WARN] Download had errors. Re-run this script to resume.
            pause
            exit /b 1
        )
    ) else (
        echo     Skipped. You can also copy model_warehouse from another
        echo     machine, or run download_models.py later.
        pause
        exit /b 1
    )
)
echo [6/6] Importing six core models into Ollama...
cd "model_warehouse\qwen2.5-7b" && ollama create qwen2.5:7b -f Modelfile
cd "..\spark-x2.5-4b" && ollama create spark-x2.5:4b -f Modelfile
cd "..\internlm3-8b" && ollama create internlm3:8b -f Modelfile
cd "..\qwen2.5-coder-7b" && ollama create qwen2.5-coder-7b:q4_k_m -f Modelfile
cd "..\deepseek-r1-8b" && ollama create deepseek-r1:8b -f Modelfile
cd "..\bge-m3" && ollama create bge-m3 -f Modelfile
cd ..
echo.
echo [Optional] Image understanding (vision model)...
set VISION_OK=0
if exist "model_warehouse\qwen2.5-vl-7b\Qwen2.5-VL-7B-Instruct-Q4_K_M.gguf" if exist "model_warehouse\qwen2.5-vl-7b\mmproj-model-f16.gguf" set VISION_OK=1
if "!VISION_OK!"=="1" goto import_vision
set /p VL=Download the optional vision model now (about 5.6 GB)? [Y/N]: 
if /i "!VL!"=="Y" goto dl_vision
echo     Skipped. Image mode will fall back to cloud VL or show a friendly hint.
goto summary
:dl_vision
echo     Downloading vision model... log: gguf\download_all.log
".venv\Scripts\python.exe" download_models.py --with-vision
if errorlevel 1 echo [WARN] Vision download failed. Re-run: python download_models.py --with-vision
if errorlevel 1 goto summary
:import_vision
echo     Importing vision model into Ollama...
cd "model_warehouse\qwen2.5-vl-7b" && ollama create qwen2.5vl:7b -f Modelfile
cd ..
echo [OK] Vision model ready (image mode available).
:summary
echo.
echo ============================================
echo   Environment summary
echo ============================================
where nvidia-smi >nul 2>nul
if errorlevel 1 echo   GPU        : nvidia-smi not found (monitor panel needs NVIDIA driver)
if not errorlevel 1 nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
where npx >nul 2>nul
if errorlevel 1 echo   Node/npx   : not found (only needed by some MCP servers)
if not errorlevel 1 echo   Node/npx   : OK
where uvx >nul 2>nul
if errorlevel 1 echo   uvx        : not found (only needed by some MCP servers)
if not errorlevel 1 echo   uvx        : OK
echo.
echo Deploy finished. Double-click the start bat to use the system.
echo   Web UI: theme, multi-session, notes, graph, search, image/copy modes
echo   Agent: 5 built-in tools + plugins/ directory + MCP (models.yaml mcp section)
pause
:no_ollama
where winget >nul 2>nul
if errorlevel 1 goto no_ollama_manual
echo [WARN] Ollama not found. Trying winget install ...
winget install --id Ollama.Ollama -e --silent --accept-package-agreements --accept-source-agreements
if errorlevel 1 goto no_ollama_manual
echo [OK] Ollama installed. Run Ollama once from the Start menu (tray icon),
echo     then double-click this script again.
pause
exit /b 0
:no_ollama_manual
echo [WARN] Auto-install failed. Download Ollama manually and run it once:
echo     https://ollama.com/download/OllamaSetup.exe
start "" "https://ollama.com/download/OllamaSetup.exe"
echo     Download page opened. Re-run this script after installing.
pause
exit /b 1