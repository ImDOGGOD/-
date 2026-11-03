@echo off
setlocal
cd /d "%~dp0"
title ZuZhiDuoMou Uninstall v2.1.1
set LOG=%~dp0uninstall_log.txt
echo ==== ZuZhiDuoMou uninstall log ==== > "%LOG%" 2>nul
if not exist "%LOG%" set LOG=%TEMP%\zzdm_uninstall.log
echo date: %date% %time% >> "%LOG%"
echo script: %~f0 >> "%LOG%"
echo. >> "%LOG%"
echo ============================================
echo   ZuZhiDuoMou  Uninstall Tool  v2.1.1
echo ============================================
echo.
if not exist "%~dp0core.py" goto no_core
echo This tool will:
echo   1. Remove the registered models in Ollama incl. optional vision
echo   2. Delete this folder and everything inside it
echo.
echo Python and Ollama themselves will NOT be removed.
echo.
set /p OK=Type YES (or Y) to uninstall, anything else to cancel: 
if /i "%OK%"=="YES" goto do_uninstall
if /i "%OK%"=="Y" goto do_uninstall
echo.
echo Cancelled. Nothing was changed.
echo cancelled by user >> "%LOG%"
pause
exit /b 0
:no_core
echo [WARN] core.py not found in THIS folder - aborting to protect files.
echo     Folder: %~dp0
echo     Tip: unzip the whole package FIRST, then run this bat from the
echo          extracted folder. Do not run it inside the ZIP.
echo core.py missing - aborted >> "%LOG%"
pause
exit /b 1
:do_uninstall
echo.
echo [1/2] Removing models from Ollama...
where ollama >nul 2>nul
if errorlevel 1 goto no_ollama
ollama rm spark-x2.5:4b >> "%LOG%" 2>&1
ollama rm qwen2.5:7b >> "%LOG%" 2>&1
ollama rm internlm3:8b >> "%LOG%" 2>&1
ollama rm qwen2.5-coder-7b:q4_k_m >> "%LOG%" 2>&1
ollama rm deepseek-r1:8b >> "%LOG%" 2>&1
ollama rm bge-m3 >> "%LOG%" 2>&1
ollama rm qwen2.5vl:7b >> "%LOG%" 2>&1
echo Models removed.
goto delete_folder
:no_ollama
echo [WARN] ollama not found - skipping model removal.
echo ollama not found >> "%LOG%"
:delete_folder
echo [2/2] Deleting project folder...
echo deleting folder: %~dp0 >> "%LOG%"
echo.
echo If this window is still open after 10 seconds, delete the folder manually:
echo   %~dp0
echo.
cd ..
start "" /b cmd /c "ping 127.0.0.1 -n 4 >nul & rd /s /q ""%~dp0"" & if exist ""%~dp0"" rd /s /q ""%~dp0"""
echo Done. This window will close in 3 seconds.
ping 127.0.0.1 -n 3 >nul
exit /b 0