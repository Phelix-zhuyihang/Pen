@echo off
chcp 65001 >nul
echo ========================================
echo   Pen 构建工具
echo ========================================
echo.
echo 请选择要执行的操作:
echo.
echo   [1] 构建 exe (pyinstaller)
echo   [2] 构建安装程序 (Inno Setup)
echo   [3] 全部构建
echo.
echo   [Q] 退出
echo.
set /p choice=请选择操作 (1/2/3/Q):

if "%choice%"=="1" goto build_exe
if "%choice%"=="2" goto build_installer
if "%choice%"=="3" goto build_all
if /i "%choice%"=="Q" goto end
if /i "%choice%"=="q" goto end

:build_exe
echo.
echo 正在构建 pen.exe ...
pyinstaller --onefile --name pen pen.py
if %errorlevel% neq 0 (
    echo 构建失败！
    pause
    goto end
)
echo.
echo 构建完成！
echo 文件位置: dist\pen.exe
goto end

:build_installer
echo.
echo 正在检查文件...
if not exist "dist\pen.exe" (
    echo 错误: 未找到 dist\pen.exe
    echo 请先运行选项 [1] 构建 exe
    pause
    goto end
)

echo.
echo 正在构建安装程序...
if not exist "installer" mkdir installer
iscc pen.iss
if %errorlevel% neq 0 (
    echo 构建失败！
    pause
    goto end
)
echo.
echo 构建完成！
echo 安装程序位置: installer\pen-setup.exe
goto end

:build_all
echo.
echo 开始完整构建流程...
echo.
echo [1/2] 构建 exe ...
pyinstaller --onefile --name pen pen.py
if %errorlevel% neq 0 (
    echo exe 构建失败！
    pause
    goto end
)

echo.
echo [2/2] 构建安装程序...
if not exist "installer" mkdir installer
iscc pen.iss
if %errorlevel% neq 0 (
    echo 安装程序构建失败！
    pause
    goto end
)

echo.
echo ========================================
echo   所有构建完成！
echo ========================================
echo   - exe 文件: dist\pen.exe
echo   - 安装程序: installer\pen-setup.exe
echo ========================================

:end
echo.
pause
