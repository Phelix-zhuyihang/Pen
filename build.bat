@echo off
echo 正在安装依赖...
pip install -r requirements.txt
pip install pyinstaller
echo.
echo 正在编译...
pyinstaller --onefile --name pen pen.py
echo.
echo 编译完成！可执行文件位于 dist\pen.exe
pause
