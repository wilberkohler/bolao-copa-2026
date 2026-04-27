@echo off
cd /d "%~dp0"
set BOLAO_HOST=127.0.0.1
set BOLAO_PORT=5000
set BOLAO_DEBUG=1
py app.py
pause
