#!/usr/bin/env python3
"""
Script pour gérer les rôles des utilisateurs
"""
from sqlalchemy.orm import Session
from api.models.user import User, UserRole
from api.core.database import SessionLocal


def list_users():
    """Liste tous les utilisateurs avec leurs rôles"""
    db = SessionLocal()
    try:
        users = db.query(User).all()

        print("\n📋 UTILISATEURS ACTUELS\n")
        print(f"{'ID':<40} {'Nom':<30} {'Role':<10}")
        print("-" * 80)

        for user in users:
            print(f"{str(user.id):<40} {user.full_name:<30} {user.role.value:<10}")

        print(f"\n✅ Total: {len(users)} utilisateurs\n")
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
        print("\nExemples:")
        print("  python scripts/manage_users.py --list")
        print("  python scripts/manage_users.py --update USER_ID admin")
        print("  python scripts/manage_users.py --set-first-admin")
