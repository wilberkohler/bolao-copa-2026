@echo off
sc.exe failure "BolaoCopa2026" reset= 86400 actions= restart/60000/restart/60000/restart/60000
sc.exe failureflag "BolaoCopa2026" 1
echo.
echo Reinicio automatico apos falha configurado para o servico BolaoCopa2026.
