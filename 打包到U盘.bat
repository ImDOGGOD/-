@echo off
cd /d "%~dp0"
title ZuZhiDuoMou Package v1.4.0
echo ============================================
echo   ZuZhiDuoMou  Package Tool  v1.4.0
echo   Copy portable package + model warehouse
echo   to a USB drive / target folder.
echo ============================================
echo.
if not exist "release" (
    echo [!] "release" folder not found.
    echo     Run this tool on the ORIGINAL computer inside the project
    echo     folder (e.g. F:\AI\local). Do NOT copy it to the USB drive.
    pause
    exit /b 1
)
if not exist "model_warehouse" (
    echo [!] "model_warehouse" folder not found.
    echo     Run this tool inside the project folder.
    pause
    exit /b 1
)
set /p DEST=Enter destination folder (e.g. E:\zuzhiduomou): 
if "%DEST%"=="" goto done
if not exist "%DEST%" mkdir "%DEST%"
copy /y "release\*.zip" "%DEST%\" >nul
if errorlevel 1 echo [!] Failed to copy portable package
xcopy /e /i /y "model_warehouse" "%DEST%\model_warehouse\" >nul
if errorlevel 1 echo [!] Failed to copy model warehouse
echo.
echo Done. Give the whole folder to the other computer.
echo There: unzip the package, keep model_warehouse inside,
echo double-click the deploy bat, then the start bat.
:done
pause