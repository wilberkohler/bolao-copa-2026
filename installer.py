#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BOLÃO COPA 2026 - Instalador Único (exe)
Compila com PyInstaller para .exe portável
"""

import os
import sys
import json
import shutil
import subprocess
import platform
import urllib.request
from pathlib import Path

class BolaoInstaller:
    def __init__(self):
        self.app_dir = Path(__file__).parent
        self.config_file = self.app_dir / "service_config.json"
        
    def header(self, text):
        """Exibe cabeçalho colorido"""
        print("\n" + "="*70)
        print(f"  {text}")
        print("="*70 + "\n")
    
    def success(self, text):
        """Mensagem de sucesso"""
        print(f"✓ {text}")
    
    def error(self, text):
        """Mensagem de erro"""
        print(f"✗ {text}")
        sys.exit(1)
    
    def info(self, text):
        """Mensagem informativa"""
        print(f"ℹ {text}")
    
    def check_python(self):
        """Verifica se Python está instalado"""
        self.info("Verificando Python...")
        
        result = subprocess.run([sys.executable, "--version"], 
                               capture_output=True, text=True)
        
        if result.returncode == 0:
            version = result.stdout.strip()
            self.success(f"{version} encontrado")
            return True
        else:
            self.error("Python não encontrado no sistema")
            return False
    
    def install_dependencies(self):
        """Instala dependências Python"""
        self.header("INSTALANDO DEPENDÊNCIAS")
        
        requirements = [
            "Flask>=3.0.0",
            "Flask-SQLAlchemy>=3.1.1",
            "pytz>=2024.1",
            "Werkzeug>=3.0.0",
            "waitress>=3.0.0",
            "pywin32>=306"
        ]
        
        self.info("Instalando pacotes Python...")
        
        for package in requirements:
            print(f"  • {package}...", end=" ", flush=True)
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-q", package],
                capture_output=True
            )
            if result.returncode == 0:
                print("✓")
            else:
                print("✗")
                self.error(f"Falha ao instalar {package}")
        
        self.success("Todas as dependências instaladas")
    
    def register_service(self):
        """Registra o serviço Windows"""
        self.header("REGISTRANDO SERVIÇO WINDOWS")
        
        try:
            self.info("Registrando BolaoCopa2026...")
            
            # Remover serviço anterior se existir
            subprocess.run(
                [sys.executable, str(self.app_dir / "windows_service.py"), "remove"],
                capture_output=True
            )
            
            # Instalar novo serviço
            result = subprocess.run(
                [sys.executable, str(self.app_dir / "windows_service.py"), 
                 "--startup", "auto", "install"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 or "already exists" in result.stderr:
                self.success("Serviço registrado com sucesso")
            else:
                self.error(f"Falha ao registrar serviço: {result.stderr}")
        
        except Exception as e:
            self.error(f"Erro ao registrar serviço: {e}")
    
    def open_firewall(self):
        """Abre porta no firewall"""
        self.header("CONFIGURANDO FIREWALL")
        
        try:
            self.info("Abrindo porta 5055...")
            
            # Remover regra anterior
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "delete", "rule", 
                 "name=Bolao Copa 2026"],
                capture_output=True
            )
            
            # Adicionar nova regra
            result = subprocess.run(
                ["netsh", "advfirewall", "firewall", "add", "rule",
                 "name=Bolao Copa 2026", "dir=in", "action=allow",
                 "protocol=tcp", "localport=5055"],
                capture_output=True
            )
            
            if result.returncode == 0:
                self.success("Porta 5055 aberta no firewall")
            else:
                self.info("Nota: Firewall pode exigir privilégios adicionais")
        
        except Exception as e:
            self.info(f"Aviso ao abrir firewall: {e}")
    
    def start_service(self):
        """Inicia o serviço"""
        self.header("INICIANDO SERVIÇO")
        
        try:
            self.info("Iniciando BolaoCopa2026...")
            
            result = subprocess.run(
                ["net", "start", "BolaoCopa2026"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 or "já foi iniciado" in result.stderr:
                self.success("Serviço iniciado com sucesso")
            else:
                self.info("Serviço não pôde ser iniciado automaticamente")
        
        except Exception as e:
            self.info(f"Aviso ao iniciar serviço: {e}")
    
    def open_browser(self):
        """Abre navegador na aplicação"""
        self.header("ABRINDO APLICAÇÃO")
        
        try:
            import webbrowser
            hostname = platform.node()
            url = f"http://{hostname}:5055"
            
            self.info(f"Abrindo {url}...")
            webbrowser.open(url)
            
            self.success(f"Aplicação disponível em: {url}")
        
        except Exception as e:
            self.info(f"Não foi possível abrir navegador: {e}")
    
    def show_summary(self):
        """Exibe resumo final"""
        self.header("✓ INSTALAÇÃO CONCLUÍDA COM SUCESSO!")
        
        hostname = platform.node()
        
        print("INFORMAÇÕES DE ACESSO:")
        print("─" * 70)
        print(f"  Serviço: Bolão Copa 2026")
        print(f"  Porta: 5055")
        print(f"  Máquina: {hostname}")
        print()
        
        print("ACESSAR A APLICAÇÃO:")
        print("─" * 70)
        print(f"  • Localmente:  http://localhost:5055")
        print(f"  • Pela rede:   http://{hostname}:5055")
        print()
        
        print("COMANDOS ÚTEIS (PowerShell):")
        print("─" * 70)
        print("  • Ver status:   Get-Service BolaoCopa2026")
        print("  • Parar:        Stop-Service BolaoCopa2026")
        print("  • Iniciar:      Start-Service BolaoCopa2026")
        print("  • Restart:      Restart-Service BolaoCopa2026")
        print()
    
    def install(self):
        """Executa instalação completa"""
        print("\n" + "╔" + "═"*68 + "╗")
        print("║" + " "*15 + "BOLÃO COPA 2026 - INSTALADOR EXE" + " "*21 + "║")
        print("╚" + "═"*68 + "╝\n")
        
        try:
            # 1. Verificar Python
            self.check_python()
            
            # 2. Instalar dependências
            self.install_dependencies()
            
            # 3. Registrar serviço
            self.register_service()
            
            # 4. Abrir firewall
            self.open_firewall()
            
            # 5. Iniciar serviço
            self.start_service()
            
            # 6. Exibir resumo
            self.show_summary()
            
            # 7. Abrir navegador
            self.open_browser()
            
            input("\nPressione Enter para fechar...")
        
        except Exception as e:
            self.error(f"Erro durante instalação: {e}")


if __name__ == "__main__":
    # Se for executado como .exe (compilado), trabalhar do diretório do exe
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))
    
    installer = BolaoInstaller()
    installer.install()
