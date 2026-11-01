@echo off
chcp 65001 >nul
title Local Multi-Agent System v1.1.1
:menu
color 0B
cls
echo.
echo  ==============================================================
echo    __       __   ______   __  __   __        __       ______
echo   /\ \     /\ \ /\  __ \ /\ \/\ \ /\ \      /\ \     /\  __ \
echo   \ \ \____\ \ \\ \ \_\ \\ \ \_\ \\ \ \     \ \ \____\ \ \_\ \
echo    \ \_____\\ \_\\ \_____\\ \_____\\ \_\     \ \_____\\ \_____\
echo     \/_____/ \/_/ \/_____/ \/_____/ \/_/      \/_____/ \/_____/
echo.
echo        ZuZhiDuoMou  (Zu Zhi Duo Mou)  v1.1.1
echo        Local Multi-Agent System
echo        Author: DeepSeek (deepseek-v4-pro)
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
".venv\Scripts\python.exe" webui.py
echo.
echo  Web UI closed. Back to menu...
pause
goto menu
:console
".venv\Scripts\python.exe" chat.py
if errorlevel 1 pause
goto menu
