@echo off
chcp 936 >nul
cd /d "%~dp0"
title 足智多谋 打包到U盘 v1.1.3
echo ============================================
echo  足智多谋 打包工具 v1.1.3
echo  把 便携包 + 模型仓库 复制到 U盘/目标文件夹
echo ============================================
echo.
if not exist "发布" (
    echo [!] 未找到"发布"文件夹。
    echo     本工具必须在【原电脑】的项目目录里运行（例如 F:\AI\local），
    echo     不要把它单独拷到 U 盘上运行。
    pause
    exit /b 1
)
if not exist "模型仓库" (
    echo [!] 未找到"模型仓库"文件夹。请在本机项目目录运行本工具。
    pause
    exit /b 1
)
set /p DEST=请输入目标文件夹（例如 E:\zuzhiduomou）: 
if "%DEST%"=="" goto done
if not exist "%DEST%" mkdir "%DEST%"
copy /y "发布\*.zip" "%DEST%\" >nul
if errorlevel 1 echo [!] 复制便携包失败
xcopy /e /i /y "模型仓库" "%DEST%\模型仓库\" >nul
if errorlevel 1 echo [!] 复制模型仓库失败
echo.
echo 完成！把整个目标文件夹拷给对方电脑即可：
echo 对方操作：解压 zip -^> 模型仓库并入 -^> 双击 安装部署.bat -^> 启动.bat
:done
pause