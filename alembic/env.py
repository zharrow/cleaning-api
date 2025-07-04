from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importer les modèles
from main import Base
from decouple import config

# Configuration Alembic
config_alembic = context.config

# Récupérer l'URL de la base de données depuis les variables d'environnement
database_url = config("DATABASE_URL", default="postgresql://user:password@localhost/cleaning_db")
config_alembic.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
if config_alembic.config_file_name is not None:
    fileConfig(config_alembic.config_file_name)

# Métadonnées pour l'autogénération
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config_alembic.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config_alembic.get_section(config_alembic.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()