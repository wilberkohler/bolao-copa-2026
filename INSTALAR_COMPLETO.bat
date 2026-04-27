@echo off
REM ============================================================================
REM INSTALAÇÃO COMPLETA - Bolão Copa 2026 (Versão Batch)
REM Script para instalação única com auto-elevação de privilégios
REM ============================================================================

setlocal enabledelayedexpansion

set "SERVICE_NAME=BolaoCopa2026"
set "DISPLAY_NAME=Bolao Copa 2026"
set "PORT=5055"
set "FIREWALL_RULE=Bolao Copa 2026"

REM Cores e símbolos
set "SUCCESS=✓"
set "ERROR=✗"
set "INFO=ℹ"

cls
echo.
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║    BOLÃO COPA 2026 - INSTALAÇÃO COMPLETA (Versão Batch v1.0)    ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.

REM Verificar se está sendo executado como admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo %INFO% Este script requer privilégios de administrador.
    echo %INFO% Aguarde enquanto o script é elevado...
    echo.
    
    REM Criar arquivo temporário para executar com elevação
    set "scriptFile=%~f0"
    set "arguments=%*"
    if "!arguments!"=="" set "arguments=install"
    
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process cmd -ArgumentList '/c \"!scriptFile!\" !arguments!' -Verb RunAs"
    exit /b 0
)

REM Parse argumentos
set "ACTION=install"
if not "%~1"=="" (
    if /i "%~1"=="remove" set "ACTION=remove"
    if /i "%~1"=="status" set "ACTION=status"
)

REM ============================================================================
REM FUNÇÕES
REM ============================================================================

if /i "%ACTION%"=="install" goto :install
if /i "%ACTION%"=="remove" goto :remove
if /i "%ACTION%"=="status" goto :status

:install
cls
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║              INICIANDO INSTALAÇÃO COMPLETA                        ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.

REM PASSO 1: Verificar Python
echo [PASSO 1] Verificando Python...
py --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo %ERROR% Python não encontrado!
    echo.
    echo Por favor, instale Python 3.8 ou superior de: https://www.python.org
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('py --version 2^>^&1') do set "PYTHON_VERSION=%%i"
echo %SUCCESS% %PYTHON_VERSION% encontrado
echo.

REM PASSO 2: Instalar dependências
echo [PASSO 2] Instalando dependências Python...
if not exist "requirements.txt" (
    color 0C
    echo %ERROR% Arquivo requirements.txt não encontrado!
    pause
    exit /b 1
)

py -m pip install --upgrade pip -q >nul 2>&1
if errorlevel 1 (
    echo %ERROR% Falha ao atualizar pip
    pause
    exit /b 1
)

py -m pip install -r requirements.txt -q >nul 2>&1
if errorlevel 1 (
    color 0C
    echo %ERROR% Falha ao instalar dependências
    echo Execute como admin e tente novamente
    pause
    exit /b 1
)

echo %SUCCESS% Dependências instaladas com sucesso
echo.

REM PASSO 3: Configurar pywin32
echo [PASSO 3] Configurando pywin32...
py -m pip install --upgrade pywin32 -q >nul 2>&1
py -m Scripts.pywin32_postinstall -install -quiet >nul 2>&1
echo %SUCCESS% pywin32 configurado
echo.

REM PASSO 4: Verificar se serviço já existe
echo [PASSO 4] Registrando serviço Windows...
sc query "%SERVICE_NAME%" >nul 2>&1
if not errorlevel 1 (
    echo %INFO% Serviço já existe. Removendo versão anterior...
    net stop "%SERVICE_NAME%" >nul 2>&1
    timeout /t 1 /nobreak >nul
    py windows_service.py remove >nul 2>&1
    timeout /t 1 /nobreak >nul
)

REM Registrar novo serviço
py windows_service.py --startup auto install >nul 2>&1
if errorlevel 1 (
    color 0C
    echo %ERROR% Falha ao registrar serviço
    pause
    exit /b 1
)
timeout /t 1 /nobreak >nul

echo %SUCCESS% Serviço registrado com sucesso
echo.

REM PASSO 5: Configurar auto-restart
echo [PASSO 5] Configurando auto-restart...
sc failure "%SERVICE_NAME%" reset= 86400 actions= restart/60000/restart/60000/restart/60000 >nul 2>&1
echo %SUCCESS% Auto-restart configurado (3 tentativas em 60s cada)
echo.

REM PASSO 6: Abrir firewall
echo [PASSO 6] Abrindo porta no Firewall...
netsh advfirewall firewall delete rule name="%FIREWALL_RULE%" >nul 2>&1
netsh advfirewall firewall add rule name="%FIREWALL_RULE%" dir=in action=allow protocol=tcp localport=%PORT% >nul 2>&1
echo %SUCCESS% Porta %PORT% aberta no firewall
echo.

REM PASSO 7: Iniciar serviço
echo [PASSO 7] Iniciando serviço...
net start "%SERVICE_NAME%" >nul 2>&1
timeout /t 2 /nobreak >nul

sc query "%SERVICE_NAME%" | find "RUNNING" >nul 2>&1
if errorlevel 1 (
    color 0E
    echo %INFO% Serviço registrado mas pode não ter iniciado
) else (
    echo %SUCCESS% Serviço iniciado com sucesso
)
echo.

REM PASSO 8: Exibir informações
cls
color 0A
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║          INSTALAÇÃO CONCLUÍDA COM SUCESSO ✓                      ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.

for /f "tokens=4" %%i in ('route print ^| findstr "\0.0.0.0"') do set "GATEWAY=%%i"

echo INFORMAÇÕES DE ACESSO:
echo ────────────────────────────────────────────────────────────────────
echo Serviço: %DISPLAY_NAME%
echo Porta: %PORT%
echo Máquina: %COMPUTERNAME%
echo.

echo ACESSAR A APLICAÇÃO:
echo ────────────────────────────────────────────────────────────────────
echo   • Localmente:     http://localhost:%PORT%
echo   • Pela rede:      http://%COMPUTERNAME%:%PORT%
echo.

echo COMANDOS ÚTEIS:
echo ────────────────────────────────────────────────────────────────────
echo   • Ver status:     sc query %SERVICE_NAME%
echo   • Parar serviço:  net stop %SERVICE_NAME%
echo   • Iniciar:        net start %SERVICE_NAME%
echo   • Remover:        %~0 remove
echo.

color 0F
pause
exit /b 0

:remove
cls
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║                       REMOVER INSTALAÇÃO                          ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.
echo %ERROR% Você está prestes a remover o serviço "%SERVICE_NAME%"
echo.
set /p CONFIRM="Deseja continuar? (s/n): "

if /i not "%CONFIRM%"=="s" (
    echo %INFO% Remoção cancelada
    exit /b 0
)

echo.
echo [PASSO 1] Parando serviço...
net stop "%SERVICE_NAME%" >nul 2>&1
timeout /t 2 /nobreak >nul
echo %SUCCESS% Serviço parado
echo.

echo [PASSO 2] Removendo serviço do registro...
py windows_service.py remove >nul 2>&1
echo %SUCCESS% Serviço removido
echo.

echo [PASSO 3] Removendo regra de firewall...
netsh advfirewall firewall delete rule name="%FIREWALL_RULE%" >nul 2>&1
echo %SUCCESS% Regra de firewall removida
echo.

cls
color 0A
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║              REMOÇÃO CONCLUÍDA COM SUCESSO ✓                      ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.
echo %INFO% O serviço "%SERVICE_NAME%" foi removido com sucesso
echo %INFO% Os arquivos da aplicação continuam na pasta atual
echo.
color 0F
pause
exit /b 0

:status
cls
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║                    STATUS DO SERVIÇO                              ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.

echo Consultando status...
sc query "%SERVICE_NAME%" >nul 2>&1
if errorlevel 1 (
    color 0C
    echo %ERROR% Serviço "%SERVICE_NAME%" não está registrado
    color 0F
) else (
    color 0A
    echo %SUCCESS% Serviço "%SERVICE_NAME%"
    color 0F
    sc query "%SERVICE_NAME%"
)

echo.
pause
exit /b 0
