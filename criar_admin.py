#!/usr/bin/env python
"""
Script de setup inicial — Cria primeiro usuário admin.
Executar uma vez na primeira vez que ligar o servidor.
"""
import sys
from app import app, db
from models import User, Grupo, Competidor

def criar_primeiro_admin():
    with app.app_context():
        # Verificar se já há admin
        admin = User.query.filter_by(eh_admin=True).first()
        if admin:
            print("✓ Já existe um usuário admin.")
            return

        print("\n" + "="*60)
        print("CRIAR PRIMEIRO USUÁRIO ADMIN")
        print("="*60)
        
        nome = input("\nNome completo: ").strip()
        email = input("E-mail: ").strip()
        apelido = input("Apelido: ").strip()
        senha = input("Senha (mín 6 caracteres): ").strip()
        
        if not all([nome, email, apelido, senha]):
            print("\n❌ Todos os campos são obrigatórios.")
            return
        
        if len(senha) < 6:
            print("\n❌ Senha muito curta (mínimo 6 caracteres).")
            return
        
        if User.query.filter_by(email=email).first():
            print("\n❌ E-mail já cadastrado.")
            return
        
        user = User(
            nome=nome,
            email=email,
            apelido=apelido,
            eh_admin=True,
            ativo=True,
        )
        user.set_password(senha)
        db.session.add(user)
        db.session.flush()

        competidor = Competidor(
            nome=nome,
            apelido=apelido,
            email=email,
            user_id=user.id,
            ativo=True,
        )
        db.session.add(competidor)
        db.session.commit()
        
        print("\n✓ Usuário admin criado com sucesso!")
        print(f"\n  E-mail: {email}")
        print(f"  Apelido: {apelido}")
        print(f"  Permissões: ADMIN")
        print("\nAgora você pode fazer login em http://127.0.0.1:5000")

if __name__ == "__main__":
    criar_primeiro_admin()
