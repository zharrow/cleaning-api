"""Add admin and manager roles

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

