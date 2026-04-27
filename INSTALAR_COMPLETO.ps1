# ============================================================================
# INSTALAÇÃO COMPLETA - Bolão Copa 2026
# Script PowerShell para instalação única com auto-elevação de privilégios
# ============================================================================

param(
    [ValidateSet("install", "remove", "status")]
    [string]$Action = "install"
)

# Cores para output
$Colors = @{
    Success = "Green"
    Error   = "Red"
    Warning = "Yellow"
    Info    = "Cyan"
}

# ============================================================================
# FUNÇÕES UTILITÁRIAS
# ============================================================================

function Write-Header {
    param([string]$Message)
    Write-Host "`n" -NoNewline
    Write-Host ("=" * 70) -ForegroundColor $Colors.Info
    Write-Host $Message -ForegroundColor $Colors.Info
    Write-Host ("=" * 70) -ForegroundColor $Colors.Info
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor $Colors.Success
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor $Colors.Error
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "! $Message" -ForegroundColor $Colors.Warning
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor $Colors.Info
}

# Verificar se está rodando como admin
function Test-IsAdmin {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Auto-elevar se necessário
function Request-AdminElevation {
    if (-not (Test-IsAdmin)) {
        Write-Header "ELEVANDO PRIVILÉGIOS"
        Write-Info "Este script requer privilégios de administrador."
        Write-Info "Aguarde enquanto o script é elevado..."
        
        $scriptPath = $MyInvocation.MyCommand.Definition
        $arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -Action $($args[0])"
        
        try {
            Start-Process PowerShell -ArgumentList $arguments -Verb RunAs
            exit 0
        }
        catch {
            Write-Error-Custom "Falha ao elevar privilégios: $_"
            exit 1
        }
    }
}

# Obter variáveis globais
function Get-ServiceInfo {
    return @{
        ServiceName     = "BolaoCopa2026"
        DisplayName     = "Bolao Copa 2026"
        Port            = 5055
        BindHost        = "0.0.0.0"
        ExecutablePath  = Join-Path $PSScriptRoot "windows_service.py"
        ConfigFile      = Join-Path $PSScriptRoot "service_config.json"
        RequirementsFile = Join-Path $PSScriptRoot "requirements.txt"
    }
}

# ============================================================================
# INSTALAÇÃO
# ============================================================================

function Install-All {
    Write-Header "INICIANDO INSTALAÇÃO COMPLETA"
    
    $info = Get-ServiceInfo
    
    # 1. Instalar dependências Python
    Write-Header "PASSO 1: INSTALANDO DEPENDÊNCIAS PYTHON"
    if (-not (Test-Path $info.RequirementsFile)) {
        Write-Error-Custom "Arquivo requirements.txt não encontrado em $($info.RequirementsFile)"
        return $false
    }
    
    try {
        Write-Info "Instalando pacotes: Flask, Flask-SQLAlchemy, Waitress, pywin32..."
        & py -m pip install --upgrade pip -q | Out-Null
        & py -m pip install -r $info.RequirementsFile -q | Out-Null
        
        # Post-install para pywin32
        Write-Info "Configurando pywin32..."
        & py -m pip install --upgrade pywin32 -q | Out-Null
        & py -m Scripts.pywin32_postinstall -install -quiet | Out-Null
        
        Write-Success "Dependências Python instaladas com sucesso"
    }
    catch {
        Write-Error-Custom "Falha ao instalar dependências: $_"
        return $false
    }
    
    # 2. Registrar serviço Windows
    Write-Header "PASSO 2: REGISTRANDO SERVIÇO WINDOWS"
    
    try {
        Write-Info "Registrando serviço '$($info.ServiceName)'..."
        
        # Remover serviço anterior se existir
        $existingService = Get-Service -Name $info.ServiceName -ErrorAction SilentlyContinue
        if ($existingService) {
            Write-Warning-Custom "Serviço '$($info.ServiceName)' já existe. Removendo versão anterior..."
            Stop-Service -Name $info.ServiceName -Force -ErrorAction SilentlyContinue
            Start-Sleep -Milliseconds 500
            & py $info.ExecutablePath --startup auto remove 2>$null
            Start-Sleep -Milliseconds 500
        }
        
        # Registrar novo serviço
        & py $info.ExecutablePath --startup auto install 2>$null
        Start-Sleep -Milliseconds 1000
        
        # Verificar se foi registrado
        $service = Get-Service -Name $info.ServiceName -ErrorAction SilentlyContinue
        if ($service) {
            Write-Success "Serviço '$($info.ServiceName)' registrado com sucesso"
        }
        else {
            Write-Error-Custom "Falha ao registrar serviço"
            return $false
        }
    }
    catch {
        Write-Error-Custom "Erro ao registrar serviço: $_"
        return $false
    }
    
    # 3. Configurar auto-restart em caso de falha
    Write-Header "PASSO 3: CONFIGURANDO AUTO-RESTART"
    
    try {
        Write-Info "Configurando reinício automático em caso de falha..."
        & sc.exe failure $info.ServiceName reset= 86400 actions= restart/60000/restart/60000/restart/60000 | Out-Null
        Write-Success "Auto-restart configurado (3 tentativas em 60s cada)"
    }
    catch {
        Write-Warning-Custom "Aviso ao configurar auto-restart: $_"
    }
    
    # 4. Abrir porta no Firewall
    Write-Header "PASSO 4: ABRINDO PORTA NO FIREWALL"
    
    try {
        Write-Info "Abrindo porta $($info.Port) no Windows Firewall..."
        
        # Remover regra anterior se existir
        & netsh advfirewall firewall delete rule name="Bolao Copa 2026" 2>$null
        Start-Sleep -Milliseconds 200
        
        # Adicionar nova regra
        & netsh advfirewall firewall add rule name="Bolao Copa 2026" dir=in action=allow protocol=tcp localport=$($info.Port) 2>$null
        
        Write-Success "Porta $($info.Port) aberta com sucesso"
    }
    catch {
        Write-Error-Custom "Falha ao abrir porta no firewall: $_"
        return $false
    }
    
    # 5. Iniciar serviço
    Write-Header "PASSO 5: INICIANDO SERVIÇO"
    
    try {
        Write-Info "Iniciando serviço '$($info.ServiceName)'..."
        Start-Service -Name $info.ServiceName -ErrorAction Stop
        Start-Sleep -Seconds 2
        
        $service = Get-Service -Name $info.ServiceName
        if ($service.Status -eq "Running") {
            Write-Success "Serviço iniciado com sucesso"
        }
        else {
            Write-Warning-Custom "Serviço registrado mas não iniciou automaticamente"
        }
    }
    catch {
        Write-Warning-Custom "Aviso ao iniciar serviço: $_"
    }
    
    # 6. Exibir informações de acesso
    Write-Header "INSTALAÇÃO CONCLUÍDA COM SUCESSO ✓"
    
    # Obter IP
    $ipAddress = (Get-NetIPAddress -AddressFamily IPv4 -AddressState Preferred -ErrorAction SilentlyContinue | 
                  Where-Object { $_.IPAddress -notmatch "^127\." } | 
                  Select-Object -First 1).IPAddress
    
    $hostName = $env:COMPUTERNAME
    
    Write-Host "`nINFORMAÇÕES DE ACESSO:" -ForegroundColor Green
    Write-Host "────────────────────────────────────────" -ForegroundColor Cyan
    Write-Info "Serviço: $($info.DisplayName)"
    Write-Info "Status: Instalado e em execução"
    Write-Info "Porta: $($info.Port)"
    Write-Info "Nome da máquina: $hostName"
    if ($ipAddress) {
        Write-Info "Endereço IP: $ipAddress"
    }
    
    Write-Host "`nACESSAR A APLICAÇÃO:" -ForegroundColor Green
    Write-Host "────────────────────────────────────────" -ForegroundColor Cyan
    Write-Host "  • Localmente:     http://localhost:$($info.Port)" -ForegroundColor Yellow
    Write-Host "  • Pela rede:      http://$hostName`:$($info.Port)" -ForegroundColor Yellow
    if ($ipAddress) {
        Write-Host "  • Por IP:         http://$ipAddress`:$($info.Port)" -ForegroundColor Yellow
    }
    
    Write-Host "`nCOMONDOS ÚTEIS:" -ForegroundColor Green
    Write-Host "────────────────────────────────────────" -ForegroundColor Cyan
    Write-Host "  • Ver status:     Get-Service BolaoCopa2026" -ForegroundColor Gray
    Write-Host "  • Parar serviço:  Stop-Service BolaoCopa2026" -ForegroundColor Gray
    Write-Host "  • Iniciar:        Start-Service BolaoCopa2026" -ForegroundColor Gray
    Write-Host "  • Logs:           Get-EventLog -LogName Application -Source BolaoCopa2026" -ForegroundColor Gray
    Write-Host "  • Remover:        .\INSTALAR_COMPLETO.ps1 -Action remove" -ForegroundColor Gray
    
    Write-Host "`n"
    return $true
}

# ============================================================================
# REMOÇÃO
# ============================================================================

function Remove-All {
    Write-Header "INICIANDO REMOÇÃO"
    
    $info = Get-ServiceInfo
    
    Write-Warning-Custom "Você está prestes a remover o serviço '$($info.ServiceName)'"
    Write-Host "`nDeseja continuar? (s/n): " -NoNewline -ForegroundColor Yellow
    
    $confirm = Read-Host
    if ($confirm -ne "s" -and $confirm -ne "S") {
        Write-Info "Remoção cancelada"
        return $true
    }
    
    # 1. Parar serviço
    Write-Header "PASSO 1: PARANDO SERVIÇO"
    
    try {
        $service = Get-Service -Name $info.ServiceName -ErrorAction SilentlyContinue
        if ($service -and $service.Status -eq "Running") {
            Write-Info "Parando serviço..."
            Stop-Service -Name $info.ServiceName -Force
            Start-Sleep -Seconds 2
            Write-Success "Serviço parado"
        }
        else {
            Write-Info "Serviço não está em execução"
        }
    }
    catch {
        Write-Warning-Custom "Aviso ao parar serviço: $_"
    }
    
    # 2. Desregistrar serviço
    Write-Header "PASSO 2: REMOVENDO SERVIÇO WINDOWS"
    
    try {
        Write-Info "Removendo serviço do registro Windows..."
        & py $info.ExecutablePath remove 2>$null
        Start-Sleep -Milliseconds 500
        Write-Success "Serviço removido do registro"
    }
    catch {
        Write-Warning-Custom "Aviso ao remover serviço: $_"
    }
    
    # 3. Remover regra de firewall
    Write-Header "PASSO 3: REMOVENDO REGRA DE FIREWALL"
    
    try {
        Write-Info "Removendo regra de firewall..."
        & netsh advfirewall firewall delete rule name="Bolao Copa 2026" 2>$null
        Write-Success "Regra de firewall removida"
    }
    catch {
        Write-Warning-Custom "Aviso ao remover regra de firewall: $_"
    }
    
    Write-Header "REMOÇÃO CONCLUÍDA ✓"
    Write-Info "O serviço '$($info.ServiceName)' foi removido com sucesso"
    Write-Info "Os arquivos da aplicação continuam em: $PSScriptRoot"
    Write-Host "`n"
    
    return $true
}

# ============================================================================
# STATUS
# ============================================================================

function Show-Status {
    Write-Header "STATUS DO SERVIÇO"
    
    $info = Get-ServiceInfo
    
    # Status do serviço
    $service = Get-Service -Name $info.ServiceName -ErrorAction SilentlyContinue
    
    if ($service) {
        Write-Info "Serviço: $($info.DisplayName)"
        Write-Info "Status: $($service.Status)"
        Write-Info "Tipo: $($service.ServiceType)"
        Write-Info "Inicialização: $($service.StartType)"
    }
    else {
        Write-Error-Custom "Serviço '$($info.ServiceName)' não está registrado"
        return
    }
    
    # Status da porta
    Write-Host "`n"
    Write-Info "Verificando porta $($info.Port)..."
    
    try {
        $netstat = netstat -ano | Select-String ":$($info.Port)"
        if ($netstat) {
            Write-Success "Porta $($info.Port) está aberta e em uso"
        }
        else {
            Write-Warning-Custom "Porta $($info.Port) não está em uso"
        }
    }
    catch {
        Write-Warning-Custom "Não foi possível verificar porta: $_"
    }
    
    # Status do firewall
    Write-Host "`n"
    Write-Info "Verificando regra de firewall..."
    
    try {
        $fwRule = & netsh advfirewall firewall show rule name="Bolao Copa 2026" 2>$null
        if ($fwRule) {
            Write-Success "Regra de firewall 'Bolao Copa 2026' está ativa"
        }
        else {
            Write-Warning-Custom "Regra de firewall 'Bolao Copa 2026' não encontrada"
        }
    }
    catch {
        Write-Warning-Custom "Não foi possível verificar firewall: $_"
    }
    
    Write-Host "`n"
}

# ============================================================================
# MAIN
# ============================================================================

# Verificar admin e elevar se necessário
Request-AdminElevation $Action

Write-Host "`n" -NoNewline
Write-Host "╔═══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         BOLÃO COPA 2026 - INSTALAÇÃO COMPLETA (v1.0)            ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

try {
    switch ($Action) {
        "install" { 
            $result = Install-All
        }
        "remove" { 
            $result = Remove-All
        }
        "status" { 
            Show-Status
            $result = $true
        }
    }
    
    if ($result) {
        exit 0
    }
    else {
        exit 1
    }
}
catch {
    Write-Error-Custom "Erro inesperado: $_"
    exit 1
}
