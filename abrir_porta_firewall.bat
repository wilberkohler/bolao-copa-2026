@echo off
netsh advfirewall firewall add rule name="Bolao Copa 2026" dir=in action=allow protocol=TCP localport=5000
echo.
echo Porta 5000 liberada no firewall do Windows.
pause
