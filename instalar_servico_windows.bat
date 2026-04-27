@echo off
net session >nul 2>&1
if %errorlevel% neq 0 (
  powershell -Command "Start-Process cmd -ArgumentList '/c cd /d \"%~dp0\" ^& instalar_servico_windows.bat' -Verb RunAs"
  exit /b
)
cd /d "%~dp0"
py -m pip install -r requirements.txt
py windows_service.py --startup auto install
py windows_service.py start
call configurar_reinicio_apos_falha.bat
echo.
echo Servico instalado e iniciado.
echo Nome do servico: BolaoCopa2026
echo Host publico configurado: NAEST202502
echo Porta configurada: 5055
pause
