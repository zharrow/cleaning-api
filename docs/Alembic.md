# 🔄 Guide Alembic - Migrations de Base de Données

Ce guide explique comment gérer les migrations Alembic dans le projet, notamment avec Docker.

## 📋 Table des matières

1. [Problème courant avec Alembic](#problème-courant-avec-alembic)
2. [Solution : Migrations manuelles](#solution--migrations-manuelles)
3. [Appliquer une migration dans Docker](#appliquer-une-migration-dans-docker)
4. [Créer une nouvelle migration](#créer-une-nouvelle-migration)
5. [Commandes utiles](#commandes-utiles)
6. [Résolution de problèmes](#résolution-de-problèmes)

---

## ⚠️ Problème courant avec Alembic

Lorsque vous essayez de générer une migration automatiquement avec :

```bash
alembic revision --autogenerate -m "description"
```

Vous pouvez rencontrer cette erreur :

```
KeyError: 'add_roles_001_add_admin_manager_roles'
```

**Cause** : Les fichiers de migration ont des références incorrectes dans leur champ `down_revision`, créant une chaîne de dépendances cassée.

---

## ✅ Solution : Migrations manuelles

### Étape 1 : Vérifier les migrations existantes

```bash
cd cleaning-api
ls alembic/versions/
```

Vous devriez voir :
- `002_rename_title_to_name.py`
- `003_add_enterprise_table.py`
- `004_add_haccp_tables.py` (celle qu'on vient de créer)

### Étape 2 : Créer une migration manuellement

Créez un fichier dans `alembic/versions/` avec le format :

```python
"""Description de la migration

Revision ID: 00X_nom_descriptif
Revises: 00Y_migration_precedente  # ⚠️ Important : référence correcte
Create Date: 2025-XX-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '00X_nom_descriptif'
down_revision = '00Y_migration_precedente'  # ⚠️ Doit correspondre exactement
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Commandes pour créer/modifier les tables
    op.create_table('ma_table',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Commandes pour annuler les changements
    op.drop_table('ma_table')
```

### Exemple concret : Migration HACCP (004_add_haccp_tables.py)

```python
"""Add HACCP tables for kitchen management

Revision ID: 004_add_haccp_tables
Revises: 003_add_enterprise_table  # ⚠️ Migration précédente
Create Date: 2025-01-10 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '004_add_haccp_tables'
down_revision = '003_add_enterprise_table'  # ⚠️ Important
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Créer les ENUMs PostgreSQL
    sa.Enum('BABIES', 'TODDLERS', 'PRESCHOOLERS', name='section').create(op.get_bind())

    # Créer les tables
    op.create_table('child',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('enterprise_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(['enterprise_id'], ['enterprises.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Créer les index
    op.create_index(op.f('ix_child_enterprise_id'), 'child', ['enterprise_id'], unique=False)


def downgrade() -> None:
    # Supprimer dans l'ordre inverse
    op.drop_index(op.f('ix_child_enterprise_id'), table_name='child')
    op.drop_table('child')
    sa.Enum('BABIES', 'TODDLERS', 'PRESCHOOLERS', name='section').drop(op.get_bind())
```

---

## 🐳 Appliquer une migration dans Docker

Le backend tourne dans Docker, donc les migrations doivent être exécutées dans le conteneur.

### Problème : Alembic n'est pas toujours installé dans le conteneur

**Solution :** Installer Alembic puis exécuter la migration

### Étapes complètes

```bash
# 1. Vérifier que les conteneurs tournent
docker ps

# Vous devriez voir :
# - cleaning-api-app    (API Python)
# - cleaning-api-db     (PostgreSQL)
# - cleaning-api-redis
# - cleaning-api-adminer

# 2. Installer Alembic dans le conteneur (si nécessaire)
docker exec cleaning-api-app sh -c "pip install alembic"

# 3. Appliquer la migration
docker exec cleaning-api-app sh -c "cd /app && /usr/local/bin/alembic upgrade head"

# 4. Vérifier que les tables ont été créées
docker exec cleaning-api-db sh -c "psql -U postgres -d cleaning_db -c \"\\dt\""
```

### Résultat attendu

Vous devriez voir toutes les tables HACCP :

```
 public | batch             | table | postgres
 public | child             | table | postgres
 public | cleaning_haccp    | table | postgres
 public | document          | table | postgres
 public | equipment         | table | postgres
 public | meal              | table | postgres
 public | meal_children     | table | postgres
 public | non_compliance    | table | postgres
 public | product           | table | postgres
 public | supplier          | table | postgres
 public | temperature       | table | postgres
```

---

## 🆕 Créer une nouvelle migration

### Option 1 : Migration manuelle (recommandée)

1. **Copier un template existant**

```bash
cp alembic/versions/004_add_haccp_tables.py alembic/versions/005_ma_nouvelle_migration.py
```

2. **Modifier le fichier**

```python
"""Description de ma nouvelle migration

Revision ID: 005_ma_nouvelle_migration
Revises: 004_add_haccp_tables  # ⚠️ Migration précédente
Create Date: 2025-XX-XX XX:XX:XX.XXXXXX

"""

revision = '005_ma_nouvelle_migration'
down_revision = '004_add_haccp_tables'  # ⚠️ Important
```

3. **Ajouter vos changements dans upgrade() et downgrade()**

4. **Appliquer la migration**

```bash
docker exec cleaning-api-app sh -c "cd /app && /usr/local/bin/alembic upgrade head"
```

### Option 2 : Auto-génération (risqué)

```bash
# ⚠️ Ne fonctionne que si la chaîne de migrations est correcte
docker exec cleaning-api-app sh -c "cd /app && alembic revision --autogenerate -m 'description'"
```

---

## 🔧 Commandes utiles

### Vérifier l'état actuel

```bash
# Version actuelle de la base de données
docker exec cleaning-api-app sh -c "cd /app && /usr/local/bin/alembic current"

# Historique des migrations
docker exec cleaning-api-app sh -c "cd /app && /usr/local/bin/alembic history"
```

### Naviguer dans les migrations

```bash
# Appliquer toutes les migrations
docker exec cleaning-api-app sh -c "cd /app && /usr/local/bin/alembic upgrade head"

# Revenir à une migration spécifique
docker exec cleaning-api-app sh -c "cd /app && /usr/local/bin/alembic downgrade 003_add_enterprise_table"

# Revenir en arrière d'une migration
docker exec cleaning-api-app sh -c "cd /app && /usr/local/bin/alembic downgrade -1"
```

### Inspecter la base de données

```bash
# Se connecter à PostgreSQL
docker exec -it cleaning-api-db psql -U postgres -d cleaning_db

# Lister toutes les tables
\dt

# Voir la structure d'une table
\d child

# Voir les ENUMs
\dT+

# Quitter
\q
```

---

## 🐛 Résolution de problèmes

### Erreur : `KeyError: 'add_roles_001_add_admin_manager_roles'`

**Cause :** Chaîne de dépendances cassée dans les fichiers de migration

**Solution :**
1. Vérifier le champ `down_revision` de chaque fichier dans `alembic/versions/`
2. S'assurer que chaque migration pointe vers la migration précédente correcte
3. Si nécessaire, supprimer les migrations problématiques et les recréer manuellement

### Erreur : `alembic: command not found`

**Cause :** Alembic n'est pas installé dans le conteneur Docker

**Solution :**
```bash
docker exec cleaning-api-app sh -c "pip install alembic"
```

### Erreur : `No module named 'alembic.__main__'`

**Cause :** Mauvaise commande d'exécution

**Solution :**
```bash
# ❌ Incorrect
docker exec cleaning-api-app python -m alembic upgrade head

# ✅ Correct
docker exec cleaning-api-app sh -c "cd /app && /usr/local/bin/alembic upgrade head"
```

### Erreur : `FATAL: role "cleaninguser" does not exist`

**Cause :** Mauvais nom d'utilisateur PostgreSQL

**Solution :**
```bash
# Utiliser postgres comme utilisateur
docker exec cleaning-api-db sh -c "psql -U postgres -d cleaning_db -c \"\\dt\""
```

### Les tables ne sont pas créées

**Vérifier :**

1. La migration est appliquée :
```bash
docker exec cleaning-api-app sh -c "cd /app && /usr/local/bin/alembic current"
```

2. Vérifier la bonne base de données :
```bash
docker exec cleaning-api-db sh -c "psql -U postgres -l"
```

3. Relancer la migration :
```bash
docker exec cleaning-api-app sh -c "cd /app && /usr/local/bin/alembic upgrade head"
```

---

## 📝 Bonnes pratiques

### ✅ À FAIRE

- **Toujours tester** la migration localement avant de la pousser
- **Créer des migrations manuellement** pour éviter les problèmes de dépendances
- **Vérifier le champ `down_revision`** pour une chaîne de dépendances correcte
- **Documenter** chaque migration avec un message descriptif
- **Tester le downgrade** pour s'assurer qu'on peut revenir en arrière
- **Vérifier les tables créées** après chaque migration

### ❌ À ÉVITER

- **Ne pas modifier** une migration déjà appliquée en production
- **Ne pas supprimer** de fichiers de migration sans réinitialiser complètement la base
- **Ne pas utiliser** `alembic revision --autogenerate` si la chaîne est cassée
- **Ne pas oublier** les index sur les foreign keys
- **Ne pas oublier** de créer les ENUMs PostgreSQL avant de les utiliser

---

## 🎯 Résumé : Migration HACCP réussie (004_add_haccp_tables)

Voici comment la migration HACCP a été appliquée avec succès :

```bash
# 1. Vérifier que Docker tourne
docker ps

# 2. Installer Alembic
docker exec cleaning-api-app sh -c "pip install alembic"

# 3. Appliquer la migration
docker exec cleaning-api-app sh -c "cd /app && /usr/local/bin/alembic upgrade head"

# 4. Vérifier les tables créées
docker exec cleaning-api-db sh -c "psql -U postgres -d cleaning_db -c \"\\dt\""
```

**Résultat :**
✅ 11 tables HACCP créées
✅ 7 ENUMs PostgreSQL créés
✅ Tous les index et foreign keys en place

---

## 📚 Ressources

- [Documentation Alembic](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

**Dernière mise à jour :** 10 janvier 2025
**Migration actuelle :** `004_add_haccp_tables`
