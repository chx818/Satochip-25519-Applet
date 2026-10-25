@echo off
setlocal
python "%~dp0tools\deploy.py" %*
exit /b %errorlevel%
