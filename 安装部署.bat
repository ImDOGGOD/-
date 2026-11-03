@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title ZuZhiDuoMou Deploy v1.9.0
echo ============================================
echo   ZuZhiDuoMou  Deploy Tool  v1.9.0
echo   Author: MoShi
echo ============================================
echo.
echo [0/4] Checking environment...
where python >nul 2>nul
if errorlevel 1 goto no_python
python -c "import sys;sys.exit(0 if sys.version_info>=(3,11) else 1)" >nul 2>nul
if errorlevel 1 goto no_python
goto check_ollama
:no_python
echo [!] Python 3.11+ (3.13 recommended) not found.
echo     Trying to install Python 3.13 with winget ...
where winget >nul 2>nul
if errorlevel 1 goto no_python_manual
winget install --id Python.Python.3.13 -e --silent --accept-package-agreements --accept-source-agreements
if errorlevel 1 goto no_python_manual
echo [OK] Python 3.13 installed. Please double-click this script again.
pause
exit /b 0
:no_python_manual
echo [!] Auto-install failed (no winget or install error).
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
echo [1/4] Creating virtual environment (if missing)...
if not exist ".venv\Scripts\python.exe" python -m venv .venv
if errorlevel 1 (
    echo [!] Failed to create venv. Check Python installation and PATH.
    pause
    exit /b 1
)
echo [2/4] Installing dependencies...
if not exist "models.yaml" copy "models.yaml.example" "models.yaml" >nul
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [!] pip install failed. Check network and retry.
    pause
    exit /b 1
)
echo [3/4] Checking model files...
if not exist "model_warehouse\qwen2.5-7b\qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf" (
    echo [!] Model files not found in model_warehouse.
    set /p DL=Download all 6 models now (about 13 GB)? [Y/N]: 
    if /i "!DL!"=="Y" (
        echo     Downloading... this takes a while. Log: gguf\download_all.log
        ".venv\Scripts\python.exe" download_models.py
        if errorlevel 1 (
            echo [!] Download had errors. Re-run this script to resume.
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
echo [4/4] Importing six models into Ollama...
cd "model_warehouse\qwen2.5-7b" && ollama create qwen2.5:7b -f Modelfile
cd "..\spark-x2.5-4b" && ollama create spark-x2.5:4b -f Modelfile
cd "..\internlm3-8b" && ollama create internlm3:8b -f Modelfile
cd "..\qwen2.5-coder-7b" && ollama create qwen2.5-coder-7b:q4_k_m -f Modelfile
cd "..\deepseek-r1-8b" && ollama create deepseek-r1:8b -f Modelfile
cd "..\bge-m3" && ollama create bge-m3 -f Modelfile
cd ..
echo.
echo Deploy finished. Double-click the start bat to use the system.
echo.
echo [Optional] Image understanding (vision mode):
echo   python download_models.py --with-vision
echo   then: cd model_warehouse\qwen2.5-vl-7b
echo   then: ollama create qwen2.5vl:7b -f Modelfile
pause
:no_ollama
where winget >nul 2>nul
if errorlevel 1 goto no_ollama_manual
echo [!] Ollama not found. Trying winget install ...
winget install --id Ollama.Ollama -e --silent --accept-package-agreements --accept-source-agreements
if errorlevel 1 goto no_ollama_manual
echo [OK] Ollama installed. Run Ollama once from the Start menu (tray icon),
echo     then double-click this script again.
pause
exit /b 0
:no_ollama_manual
echo [!] Auto-install failed. Download Ollama manually and run it once:
echo     https://ollama.com/download/OllamaSetup.exe
start "" "https://ollama.com/download/OllamaSetup.exe"
echo     Download page opened. Re-run this script after installing.
pause
exit /b 1