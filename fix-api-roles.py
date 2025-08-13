#!/usr/bin/env python3
"""
Script pour corriger les rôles dans l'API et la base de données
"""
import os
import sys
from pathlib import Path

# === PARTIE 1: METTRE À JOUR LE MODÈLE USER ===

def update_user_model():
    """Met à jour le modèle User pour inclure tous les rôles"""
    
    user_model_path = Path("api/models/user.py")
    
    new_content = '''from sqlalchemy import Column, String, Enum
from enum import Enum as PyEnum
from api.models.base import TimestampedModel

class UserRole(PyEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    GERANTE = "gerante"  # Alias pour manager

class User(TimestampedModel):
    __tablename__ = "users"
    
    firebase_uid = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.GERANTE)
'''
    
    print("📝 Mise à jour du modèle User...")
    user_model_path.write_text(new_content)
    print("✅ Modèle User mis à jour avec les 3 rôles")

# === PARTIE 2: METTRE À JOUR LES DÉPENDANCES D'AUTH ===

def update_auth_dependencies():
    """Met à jour les dépendances d'authentification"""
    
    auth_deps_path = Path("api/core/auth_dependencies.py")
    
    new_content = '''from typing import Optional
from fastapi import Depends, HTTPException, status
from api.models.user import User, UserRole
from api.core.security import get_current_user

class RequireRole:
    """Dependency pour vérifier le rôle de l'utilisateur"""
    
    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rôle insuffisant. Rôles autorisés: {[r.value for r in self.allowed_roles]}"
            )
        return current_user

# Helpers pour les rôles
require_admin = RequireRole([UserRole.ADMIN])
require_manager = RequireRole([UserRole.ADMIN, UserRole.MANAGER, UserRole.GERANTE])
require_gerante = RequireRole([UserRole.ADMIN, UserRole.MANAGER, UserRole.GERANTE])

# Alias pour la compatibilité
require_management = require_manager
'''
    
    print("📝 Mise à jour des dépendances d'authentification...")
    auth_deps_path.write_text(new_content)
    print("✅ Dépendances d'authentification mises à jour")

# === PARTIE 3: METTRE À JOUR LE SCHÉMA USER ===

def update_user_schema():
    """Met à jour le schéma Pydantic User"""
    
    schema_path = Path("api/schemas/user.py")
    
    new_content = '''import uuid
from datetime import datetime
from pydantic import BaseModel
from api.models.user import UserRole

class UserCreate(BaseModel):
    firebase_uid: str
    full_name: str
    role: UserRole = UserRole.GERANTE

class UserUpdate(BaseModel):
    full_name: str | None = None
    role: UserRole | None = None

class UserResponse(BaseModel):
    id: uuid.UUID
    firebase_uid: str
    full_name: str
    role: UserRole
    created_at: datetime
    
    class Config:
        from_attributes = True
'''
    
    print("📝 Mise à jour du schéma User...")
    schema_path.write_text(new_content)
    print("✅ Schéma User mis à jour")

# === PARTIE 4: CRÉER UN FICHIER DE MIGRATION ALEMBIC ===

def create_migration():
    """Crée un fichier de migration Alembic"""
    
    migration_content = '''"""Add admin and manager roles

Revision ID: add_roles_001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_roles_001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Modifier l'enum pour ajouter les nouveaux rôles
    op.execute("ALTER TYPE userrole RENAME TO userrole_old")
    
    # Créer le nouvel enum avec tous les rôles
    op.execute("CREATE TYPE userrole AS ENUM ('admin', 'manager', 'gerante')")
    
    # Mettre à jour la colonne pour utiliser le nouvel enum
    op.execute("""
        ALTER TABLE users 
        ALTER COLUMN role TYPE userrole 
        USING role::text::userrole
    """)
    
    # Supprimer l'ancien enum
    op.execute("DROP TYPE userrole_old")
    
    print("✅ Enum UserRole mis à jour avec les rôles: admin, manager, gerante")

def downgrade():
    # Revenir à l'ancien enum
    op.execute("ALTER TYPE userrole RENAME TO userrole_old")
    op.execute("CREATE TYPE userrole AS ENUM ('gerante')")
    op.execute("""
        ALTER TABLE users 
        ALTER COLUMN role TYPE userrole 
        USING CASE 
            WHEN role::text IN ('admin', 'manager') THEN 'gerante'::userrole 
            ELSE role::text::userrole 
        END
    """)
    op.execute("DROP TYPE userrole_old")
'''
    
    # Créer le dossier de migrations si nécessaire
    migrations_dir = Path("alembic/versions")
    migrations_dir.mkdir(parents=True, exist_ok=True)
    
    migration_file = migrations_dir / "add_roles_001_add_admin_manager_roles.py"
    
    print("📝 Création de la migration Alembic...")
    migration_file.write_text(migration_content)
    print(f"✅ Migration créée: {migration_file}")
    
    return migration_file

# === PARTIE 5: SCRIPT DE MISE À JOUR DES UTILISATEURS ===

def create_user_update_script():
    """Crée un script pour mettre à jour les utilisateurs existants"""
    
    script_content = '''#!/usr/bin/env python3
"""
Script pour gérer les rôles des utilisateurs
"""
import asyncio
from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import Session
from api.core.config import settings
from api.models.user import User, UserRole
from api.core.database import SessionLocal
import sys

def list_users():
    """Liste tous les utilisateurs avec leurs rôles"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        
        print("\\n📋 UTILISATEURS ACTUELS\\n")
        print(f"{'ID':<40} {'Email/Name':<30} {'Role':<10}")
        print("-" * 80)
        
        for user in users:
            print(f"{str(user.id):<40} {user.full_name:<30} {user.role.value:<10}")
        
        print(f"\\n✅ Total: {len(users)} utilisateurs\\n")
    finally:
        db.close()

def update_user_role(user_id: str, new_role: str):
    """Met à jour le rôle d'un utilisateur"""
    db = SessionLocal()
    try:
        # Vérifier que le rôle est valide
        try:
            role = UserRole(new_role)
        except ValueError:
            print(f"❌ Rôle invalide: {new_role}")
            print(f"   Rôles valides: {[r.value for r in UserRole]}")
            return False
        
        # Chercher l'utilisateur
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            # Essayer par firebase_uid
            user = db.query(User).filter(User.firebase_uid == user_id).first()
        
        if not user:
            print(f"❌ Utilisateur non trouvé: {user_id}")
            return False
        
        # Mettre à jour le rôle
        old_role = user.role
        user.role = role
        db.commit()
        
        print(f"✅ Rôle mis à jour pour {user.full_name}:")
        print(f"   {old_role.value} → {role.value}")
        return True
    finally:
        db.close()

def set_first_user_as_admin():
    """Définit le premier utilisateur comme admin"""
    db = SessionLocal()
    try:
        first_user = db.query(User).order_by(User.created_at).first()
        if first_user:
            first_user.role = UserRole.ADMIN
            db.commit()
            print(f"✅ {first_user.full_name} est maintenant ADMIN")
            return True
        else:
            print("❌ Aucun utilisateur trouvé")
            return False
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Gestion des rôles utilisateurs")
    parser.add_argument("--list", action="store_true", help="Lister tous les utilisateurs")
    parser.add_argument("--update", nargs=2, metavar=("USER_ID", "ROLE"), 
                       help="Mettre à jour le rôle d'un utilisateur")
    parser.add_argument("--set-first-admin", action="store_true", 
                       help="Définir le premier utilisateur comme admin")
    
    args = parser.parse_args()
    
    if args.list:
        list_users()
    elif args.update:
        update_user_role(args.update[0], args.update[1])
    elif args.set_first_admin:
        set_first_user_as_admin()
    else:
        parser.print_help()
        print("\\nExemples:")
        print("  python manage_users.py --list")
        print("  python manage_users.py --update USER_ID admin")
        print("  python manage_users.py --set-first-admin")
'''
    
    script_path = Path("scripts/manage_users.py")
    script_path.parent.mkdir(exist_ok=True)
    
    print("📝 Création du script de gestion des utilisateurs...")
    script_path.write_text(script_content)
    script_path.chmod(0o755)  # Rendre exécutable
    print(f"✅ Script créé: {script_path}")
    
    return script_path

# === EXECUTION PRINCIPALE ===

def main():
    print("\n🚀 CORRECTION DES RÔLES DANS L'API\n")
    
    # Vérifier qu'on est dans le bon dossier
    if not Path("api").exists():
        print("❌ Le dossier 'api' n'existe pas. Êtes-vous dans le bon répertoire ?")
        sys.exit(1)
    
    try:
        # 1. Mettre à jour les fichiers Python
        update_user_model()
        update_auth_dependencies()
        update_user_schema()
        
        # 2. Créer la migration
        migration_file = create_migration()
        
        # 3. Créer le script de gestion
        user_script = create_user_update_script()
        
        print("\n" + "="*60)
        print("✅ MISE À JOUR TERMINÉE")
        print("="*60)
        
        print("\n📋 PROCHAINES ÉTAPES:\n")
        print("1. Appliquer la migration à la base de données:")
        print("   alembic upgrade head\n")
        
        print("2. Lister les utilisateurs actuels:")
        print("   python scripts/manage_users.py --list\n")
        
        print("3. Mettre à jour les rôles (exemples):")
        print("   python scripts/manage_users.py --set-first-admin")
        print("   python scripts/manage_users.py --update USER_ID admin\n")
        
        print("4. Redémarrer l'API:")
        print("   python -m api.main\n")
        
        print("5. Tester l'accès aux pages /manage/* dans l'application")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
