# alembic/env.py - CONFIGURATION CORRIGÉE POUR UNICODE
import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# === FIX UNICODE POUR WINDOWS ===
# Forcer l'encodage UTF-8
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# Ajouter le répertoire racine au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models.base import Base
from api.core.config import settings

# Configuration Alembic
config = context.config

# Configurer les logs si le fichier de config existe
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Métadonnées des modèles
target_metadata = Base.metadata

def get_database_url():
    """
    Récupère l'URL de la base de données avec encodage UTF-8 forcé
    """
    # Utiliser les settings du projet
    # db_url = settings.DATABASE_URL
    db_url = "postgresql://username:password@localhost:5432/cleaning_db"
    
    # Forcer l'encodage UTF-8 si pas déjà présent
    if "client_encoding" not in db_url:
        separator = "&" if "?" in db_url else "?"
        db_url = f"{db_url}{separator}*"
    
    return db_url

def run_migrations_offline() -> None:
    """
    Exécuter les migrations en mode 'offline'
    """
    url = get_database_url()
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """
    Exécuter les migrations en mode 'online'
    """
    # Configuration pour forcer UTF-8
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_database_url()
    
    # Options supplémentaires pour PostgreSQL + UTF-8
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        # Options pour forcer UTF-8
        # connect_args={
        #     "client_encoding": "utf8",
        #     "options": "-c timezone=UTC"
        # }
    )

    # with connectable.connect() as connection:
    #     context.configure(
    #         connection=connection,
    #         target_metadata=target_metadata,
    #         compare_type=True,
    #         compare_server_default=True,
    #     )

    #     with context.begin_transaction():
    #         context.run_migrations()

# Exécution
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()