@echo off
chcp 936 >nul
cd /d "%~dp0"
title 足智多谋 一键卸载 v1.1.3
echo ============================================
echo  足智多谋 一键卸载工具
echo ============================================
echo.
if not exist "%~dp0core.py" (
    echo [!] 当前文件夹不像是足智多谋项目目录（缺少 core.py），
    echo     为防止误删已中止。请在足智多谋项目目录里运行本工具。
    pause
    exit /b 1
)
echo 本工具将执行：
echo   1. 从 Ollama 删除足智多谋注册的 6 个模型
echo   2. 删除本文件夹及其全部内容（代码 / 数据 / 虚拟环境）
echo.
echo 不会卸载 Python 和 Ollama 本身（如需请到系统"应用"里单独卸载）。
echo.
set /p OK=确认卸载？输入 YES 继续，其他任意键取消: 
if not "%OK%"=="YES" (
    echo.
    echo 已取消，未做任何更改。
    pause
    exit /b 0
)
echo.
echo [1/2] 从 Ollama 删除模型...
where ollama >nul 2>nul
if errorlevel 1 (
    echo [!] 未找到 ollama 命令，跳过模型删除。
) else (
    ollama rm spark-x2.5:4b
    ollama rm qwen2.5:7b
    ollama rm internlm3:8b
    ollama rm qwen2.5-coder-7b:q4_k_m
    ollama rm deepseek-r1:8b
    ollama rm bge-m3
    echo 模型删除完成。
)
echo [2/2] 删除项目文件夹...
cd ..
start /b cmd /c "ping 127.0.0.1 -n 4 >nul & rmdir /s /q ""%~dp0"""
echo.
echo 卸载完成，本窗口 3 秒后自动关闭。
ping 127.0.0.1 -n 3 >nul
exit /b 0