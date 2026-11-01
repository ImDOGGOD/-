@echo off
chcp 65001 >nul
title ZuZhiDuoMou - Package to USB
echo ============================================
echo  Copy portable package + model warehouse
echo  to a USB drive / shared folder for delivery.
echo ============================================
echo.
set /p DEST="Enter destination folder (e.g. E:\zuzhiduomou): "
if "%DEST%"=="" goto done
if not exist "%DEST%" mkdir "%DEST%"
copy /y "发布\足智多谋_v1.1.1_便携包.zip" "%DEST%\" >nul
xcopy /e /i /y "模型仓库" "%DEST%\模型仓库\" >nul
echo.
echo  Done. Give the whole folder to the other computer:
echo  on that machine, unzip the package, keep the model
echo  warehouse folder inside, run install.bat, then start.bat.
:done
pause
