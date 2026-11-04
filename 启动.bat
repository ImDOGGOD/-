@echo off
cd /d "%~dp0"
chcp 65001 >nul
title ZuZhiDuoMou v2.1.6
:menu
color 0B
cls
echo.
echo  ==============================================================
echo    ZuZhiDuoMou  (Zu Zhi Duo Mou)  v2.1.6
echo    Local Multi-Agent System
echo    Author: MoShi
echo.
echo        [1] Web UI   - chat in your browser (recommended)
echo        [2] Console  - chat in this window
echo        [3] Manual   - open README.md
echo        [4] Exit
echo  ==============================================================
echo.
choice /c 1234 /n /m "        Choose [1/2/3/4]: "
if errorlevel 4 exit /b 0
if errorlevel 3 start "" "README.md" & goto menu
if errorlevel 2 goto console
goto web

:web
call :ensure_ollama
if errorlevel 1 goto menu
".venv\Scripts\python.exe" webui.py
echo.
echo  Web UI closed. Back to menu...
pause
goto menu

:console
call :ensure_ollama
if errorlevel 1 goto menu
".venv\Scripts\python.exe" chat.py
if errorlevel 1 pause
goto menu

:ensure_ollama
".venv\Scripts\python.exe" ollama_check.py >nul 2>nul
if not errorlevel 1 goto ollama_ok
echo.
echo  [INFO] Ollama is not running. Starting it...
call :start_ollama
if errorlevel 1 goto no_ollama
set OLLAMA_WAIT=0
:poll_ollama
".venv\Scripts\python.exe" ollama_check.py >nul 2>nul
if not errorlevel 1 goto ollama_ok
set /a OLLAMA_WAIT+=1
if %OLLAMA_WAIT% geq 30 goto ollama_timeout
ping 127.0.0.1 -n 2 >nul
goto poll_ollama

:start_ollama
if exist "%LOCALAPPDATA%\Programs\Ollama\ollama app.exe" goto start_app_local
if exist "%ProgramFiles%\Ollama\ollama app.exe" goto start_app_pf
where ollama >nul 2>nul
if errorlevel 1 exit /b 1
start "Ollama Service" /min cmd /c "ollama serve"
exit /b 0
:start_app_local
start "" "%LOCALAPPDATA%\Programs\Ollama\ollama app.exe"
exit /b 0
:start_app_pf
start "" "%ProgramFiles%\Ollama\ollama app.exe"
exit /b 0

:ollama_ok
echo  [OK] Ollama is running.
exit /b 0

:ollama_timeout
echo.
echo  [WARN] Ollama did not start within 30 seconds.
echo         Please start the Ollama app from the Start Menu and retry.
pause
exit /b 1

:no_ollama
echo.
echo  [WARN] ollama not found.
echo         Install Ollama from: https://ollama.com/download
pause
exit /b 1