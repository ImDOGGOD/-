@echo off
title ZuZhiDuoMou Stop v2.1.5
echo ============================================
echo   ZuZhiDuoMou  Stop Web UI
echo ============================================
echo.
echo Closing the Web UI on port 8765 ...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8765" ^| findstr "LISTENING"') do taskkill /PID %%a /F >nul 2>&1
echo.
echo Done. If no process was listed above, the Web UI was not running.
echo.
echo Tip: normally just close the console window that started the Web UI
echo (the black window titled ZuZhiDuoMou). This tool is a fallback.
echo.
pause