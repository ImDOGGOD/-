@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title ZuZhiDuoMou Diagnosis v2.1.2
set LOG=%~dp0zzdm_diag.txt
echo ==== ZuZhiDuoMou diagnosis ==== > "%LOG%" 2>nul
if not exist "%LOG%" set LOG=%TEMP%\zzdm_diag.log
echo date: %date% %time% >> "%LOG%"
echo cwd: %CD% >> "%LOG%"
echo script: %~f0 >> "%LOG%"
echo. >> "%LOG%"
echo --- OS --- >> "%LOG%"
ver >> "%LOG%" 2>&1
echo. >> "%LOG%"
echo --- project files --- >> "%LOG%"
if exist core.py (echo core.py: OK >> "%LOG%") else (echo core.py: MISSING >> "%LOG%")
if exist webui.py (echo webui.py: OK >> "%LOG%") else (echo webui.py: MISSING >> "%LOG%")
if exist models.yaml (echo models.yaml: OK >> "%LOG%") else (echo models.yaml: MISSING ^(run deploy bat^) >> "%LOG%")
if exist .venv\Scripts\python.exe (echo venv: OK >> "%LOG%") else (echo venv: MISSING ^(run deploy bat^) >> "%LOG%")
if exist model_warehouse\qwen2.5-7b (echo model_warehouse: OK >> "%LOG%") else (echo model_warehouse: MISSING >> "%LOG%")
echo. >> "%LOG%"
echo --- tools --- >> "%LOG%"
where python >> "%LOG%" 2>&1
where ollama >> "%LOG%" 2>&1
where nvidia-smi >> "%LOG%" 2>&1
where node >> "%LOG%" 2>&1
where npx >> "%LOG%" 2>&1
where uvx >> "%LOG%" 2>&1
echo. >> "%LOG%"
echo --- cmd echo test --- >> "%LOG%"
echo diag-test-ok >> "%LOG%"
echo. >> "%LOG%"
echo Done. Log file: %LOG%
echo.
echo --- log content ---
type "%LOG%"
echo -------------------
echo.
echo Send this log file to the developer if anything failed.
pause