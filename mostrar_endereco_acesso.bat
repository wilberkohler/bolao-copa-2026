@echo off
echo.
echo Enderecos IPv4 desta maquina:
ipconfig | findstr /R /C:"IPv4" /C:"Endere.o IPv4"
echo.
echo Acesse o sistema pelo navegador em: http://NAEST202502:5055
echo Ou substitua pelo IPv4 exibido acima: http://IP_DA_MAQUINA:5055
pause
