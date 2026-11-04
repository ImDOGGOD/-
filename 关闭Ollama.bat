@echo off
title ZuZhiDuoMou Stop Ollama v2.1.6
echo ============================================
echo   ZuZhiDuoMou  Stop Ollama
echo ============================================
echo.
echo Closing Ollama processes ...
taskkill /F /IM "ollama app.exe" >nul 2>&1
taskkill /F /IM ollama.exe >nul 2>&1
echo.
echo Done. Ollama processes stopped.
echo.
echo Tip: to also stop the Web UI, run the Stop Web tool.
echo.
pause