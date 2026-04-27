#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para compilar a aplicação Bolão Copa 2026 em um .EXE único
Usa PyInstaller para gerar o executável
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def print_success(text):
    print(f"✓ {text}")

def print_error(text):
    print(f"✗ {text}")
    sys.exit(1)

def print_info(text):
    print(f"ℹ {text}")

# Detectar diretório
SCRIPT_DIR = Path(__file__).parent
APP_DIR = SCRIPT_DIR
BUILD_DIR = APP_DIR / "build_exe"
DIST_DIR = APP_DIR / "dist"

print("\n" + "╔" + "═"*68 + "╗")
print("║" + " "*10 + "COMPILADOR - BOLÃO COPA 2026 para .EXE" + " "*18 + "║")
print("╚" + "═"*68 + "╝")

# PASSO 1: Instalar PyInstaller
print_header("PASSO 1: INSTALANDO PYINSTALLER")

print_info("Instalando PyInstaller...")
result = subprocess.run(
    [sys.executable, "-m", "pip", "install", "-q", "pyinstaller"],
    capture_output=True
)

if result.returncode != 0:
    print_error("Falha ao instalar PyInstaller")
else:
    print_success("PyInstaller instalado")

# PASSO 2: Preparar diretórios
print_header("PASSO 2: PREPARANDO DIRETÓRIOS")

if BUILD_DIR.exists():
    print_info(f"Removendo {BUILD_DIR}...")
    shutil.rmtree(BUILD_DIR)

if DIST_DIR.exists():
    print_info(f"Limpando {DIST_DIR}...")
    shutil.rmtree(DIST_DIR)

BUILD_DIR.mkdir(exist_ok=True)
print_success("Diretórios preparados")

# PASSO 3: Compilar com PyInstaller
print_header("PASSO 3: COMPILANDO PARA .EXE")

# Lista de arquivos a incluir
hidden_imports = [
    "flask",
    "flask_sqlalchemy",
    "pytz",
    "werkzeug",
    "waitress",
    "pywin32",
]

pyinstaller_args = [
    sys.executable,
    "-m",
    "PyInstaller",
    "--onefile",                                    # Um único arquivo
    "--name", "BolaoInstalador",                   # Nome do exe
    "--distpath", str(DIST_DIR),                   # Output dir
    "--workpath", str(BUILD_DIR / "work"),         # Work dir
    "--specpath", str(BUILD_DIR),                  # Spec dir
]

# Adicionar icon se existir
if (APP_DIR / "static/favicon.ico").exists():
    pyinstaller_args.extend(["--icon", str(APP_DIR / "static/favicon.ico")])

# Adicionar imports ocultos
for imp in hidden_imports:
    pyinstaller_args.extend(["--hidden-import", imp])

# Adicionar dados (templates, static)
pyinstaller_args.extend([
    "--add-data", f"{APP_DIR}/templates:templates",
    "--add-data", f"{APP_DIR}/static:static",
    "--collect-all", "flask",
    "--collect-all", "flask_sqlalchemy",
])

# Arquivo a compilar
pyinstaller_args.append(str(APP_DIR / "installer.py"))

print_info(f"Compilando: installer.py")
print_info("Isso pode levar alguns minutos...")

result = subprocess.run(pyinstaller_args, capture_output=False, text=True)

if result.returncode != 0:
    print_error("Falha na compilação com PyInstaller")
else:
    print_success("Compilação concluída")

# PASSO 4: Copiar arquivos necessários para perto do .exe
print_header("PASSO 4: EMPACOTANDO ARQUIVOS")

exe_path = DIST_DIR / "BolaoInstalador.exe"

if not exe_path.exists():
    print_error(f"Arquivo {exe_path} não foi criado")

print_info(f"Executável criado: {exe_path}")

# Copiar arquivos essenciais
files_to_copy = [
    "app.py",
    "models.py",
    "scoring.py",
    "wsgi.py",
    "windows_service.py",
    "service_runner.py",
    "runtime_config.py",
    "requirements.txt",
    "service_config.json",
    "seed_jogos_copa_2026.py",
]

for file in files_to_copy:
    src = APP_DIR / file
    dst = DIST_DIR / file
    if src.exists():
        print_info(f"Copiando {file}...")
        shutil.copy2(src, dst)

# Copiar diretórios
for directory in ["templates", "static"]:
    src = APP_DIR / directory
    dst = DIST_DIR / directory
    if src.exists():
        print_info(f"Copiando pasta {directory}/...")
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)

print_success("Arquivos empacotados")

# PASSO 5: Exibir resumo
print_header("✓ COMPILAÇÃO CONCLUÍDA COM SUCESSO!")

print("ARQUIVO GERADO:")
print("─" * 70)
print(f"  {exe_path}")
print(f"  Tamanho: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
print()

print("PRÓXIMOS PASSOS:")
print("─" * 70)
print("  1. Copie a pasta 'dist' inteira para sua máquina de destino")
print("  2. Clique duplo em 'BolaoInstalador.exe'")
print("  3. O instalador fará tudo automaticamente!")
print("  4. Não precisa ter Python instalado!")
print()

print("DISTRIBUIÇÃO:")
print("─" * 70)
print(f"  Pasta: {DIST_DIR}")
print("  Tamanho total recomendado para zip: ~150-200 MB")
print()

print("DICAS:")
print("─" * 70)
print("  • O .exe é portável, pode colocar em pen drive")
print("  • Compartilhe toda a pasta 'dist' no SharePoint")
print("  • Ou crie um .zip para download")
print()

input("Pressione Enter para fechar...")
