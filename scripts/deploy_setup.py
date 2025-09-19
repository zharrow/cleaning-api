#!/usr/bin/env python3
"""
Script de configuration post-déploiement pour cLean Backend
Exécute les migrations et initialise les données de base
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(command: str, description: str):
    """Exécute une commande et affiche le résultat"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✅ {description} - Succès")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Erreur: {e}")
        if e.stdout:
            print(f"   Stdout: {e.stdout}")
        if e.stderr:
            print(f"   Stderr: {e.stderr}")
        return False

def main():
    """Script principal de déploiement"""
    print("🚀 Démarrage du script de déploiement cLean Backend")

    # Vérifier les variables d'environnement
    required_env_vars = ["DATABASE_URL", "FIREBASE_PROJECT_ID"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        print(f"❌ Variables d'environnement manquantes: {', '.join(missing_vars)}")
        sys.exit(1)

    print("✅ Variables d'environnement OK")

    # Exécuter les migrations Alembic
    if not run_command("alembic upgrade head", "Exécution des migrations de base de données"):
        print("❌ Échec des migrations. Arrêt du déploiement.")
        sys.exit(1)

    # Initialiser les données de base (si le script existe)
    seed_script = Path("scripts/seed_data.py")
    if seed_script.exists():
        if not run_command("python scripts/seed_data.py", "Initialisation des données de base"):
            print("⚠️  Échec de l'initialisation des données (non critique)")
    else:
        print("ℹ️  Pas de script d'initialisation des données trouvé")

    print("🎉 Déploiement terminé avec succès!")
    print("🔗 L'API est prête à recevoir des requêtes")

if __name__ == "__main__":
    main()