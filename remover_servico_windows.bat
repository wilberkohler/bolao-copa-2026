@echo off
net session >nul 2>&1
if %errorlevel% neq 0 (
  powershell -Command "Start-Process cmd -ArgumentList '/c cd /d \"%~dp0\" ^& remover_servico_windows.bat' -Verb RunAs"
  exit /b
)
cd /d "%~dp0"
py windows_service.py stop
py windows_service.py remove
echo.
echo Servico removido.
pause
