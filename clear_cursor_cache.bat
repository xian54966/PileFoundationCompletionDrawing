@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo 正在清理 Cursor 缓存文件...

:: 检查 Cursor 是否正在运行
tasklist /FI "IMAGENAME eq Cursor.exe" 2>NUL | find /I /N "Cursor.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo 正在停止 Cursor 进程...
    taskkill /F /IM "Cursor.exe" 2>nul
    timeout /t 2 /nobreak >nul
) else (
    echo Cursor 未在运行，继续清理...
)

:: 设置 Cursor 缓存目录
set "CURSOR_CACHE=%LOCALAPPDATA%\Programs\Cursor\resources\app\cache"
set "CURSOR_EXTENSIONS=%USERPROFILE%\.cursor\extensions"

:: 清理缓存文件
echo 正在清理缓存目录...
if exist "%CURSOR_CACHE%" (
    rd /s /q "%CURSOR_CACHE%" 2>nul
    echo 已清理主缓存目录
) else (
    echo 主缓存目录不存在，跳过
)

:: 清理扩展缓存
echo 正在清理扩展缓存...
if exist "%CURSOR_EXTENSIONS%" (
    rd /s /q "%CURSOR_EXTENSIONS%" 2>nul
    echo 已清理扩展缓存目录
) else (
    echo 扩展缓存目录不存在，跳过
)

:: 清理临时文件
echo 正在清理临时文件...
if exist "%TEMP%" (
    del /f /q "%TEMP%\cursor*.*" 2>nul
    del /f /q "%TEMP%\*cursor*.*" 2>nul
    echo 已清理临时文件
) else (
    echo 临时目录不存在，跳过
)

echo.
echo 清理完成！
echo 请重新启动 Cursor 以应用更改。
echo.
pause 