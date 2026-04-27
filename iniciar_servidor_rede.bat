@echo off
cd /d "%~dp0"
set BOLAO_HOST=0.0.0.0
set BOLAO_PORT=5000
set BOLAO_DEBUG=0
py app.py
echo.
echo Servidor disponivel na rede local na porta 5000.
echo Descubra o IP desta maquina com: ipconfig
pause
