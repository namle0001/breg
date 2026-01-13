@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "PYTHONPATH=%SCRIPT_DIR%\breg;%PYTHONPATH%"

python "%SCRIPT_DIR%\breg\main.py" %*