@echo off
cd /d "%~dp0"
title ZuZhiDuoMou Uninstall v1.4.0
echo ============================================
echo   ZuZhiDuoMou  Uninstall Tool
echo ============================================
echo.
if not exist "%~dp0core.py" (
    echo [!] This folder does not look like the ZuZhiDuoMou project
    echo     (core.py missing). Aborting to avoid deleting the wrong folder.
    pause
    exit /b 1
)
echo This tool will:
echo   1. Remove the 6 models registered in Ollama
echo   2. Delete this folder and everything inside it
echo.
echo Python and Ollama themselves will NOT be removed.
echo.
set /p OK=Type YES to uninstall, anything else to cancel: 
if not "%OK%"=="YES" (
    echo.
    echo Cancelled. Nothing was changed.
    pause
    exit /b 0
)
echo.
echo [1/2] Removing models from Ollama...
where ollama >nul 2>nul
if errorlevel 1 (
    echo [!] ollama command not found, skipping model removal.
) else (
    ollama rm spark-x2.5:4b
    ollama rm qwen2.5:7b
    ollama rm internlm3:8b
    ollama rm qwen2.5-coder-7b:q4_k_m
    ollama rm deepseek-r1:8b
    ollama rm bge-m3
    echo Models removed.
)
echo [2/2] Deleting project folder...
cd ..
start /b cmd /c "ping 127.0.0.1 -n 4 >nul & rmdir /s /q ""%~dp0"""
echo.
echo Done. This window will close in 3 seconds.
ping 127.0.0.1 -n 3 >nul
exit /b 0