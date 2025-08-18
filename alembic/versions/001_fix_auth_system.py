# alembic/versions/001_fix_auth_system.py
"""Fix auth system and add performers

Revision ID: fix_auth_001
Revises: 
Create Date: 2024-08-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'fix_auth_001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """
    Mise à jour vers le nouveau système d'authentification
    """
    
    # 1. Modifier la table users si elle existe déjà
    try:
        # Ajouter la colonne is_active si elle n'existe pas
        op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
        
        # Modifier l'enum des rôles
        # Créer le nouveau type enum
        op.execute("CREATE TYPE new_userrole AS ENUM ('admin', 'gerante', 'performer')")
        
        # Migrer les données existantes
        op.execute("""
            UPDATE users 
            SET role = CASE 
                WHEN role = 'manager' THEN 'gerante'::new_userrole
                WHEN role = 'admin' THEN 'admin'::new_userrole
                ELSE 'gerante'::new_userrole
            END::text::new_userrole
        """)
        
        # Remplacer l'ancien type
        op.execute("ALTER TABLE users ALTER COLUMN role TYPE new_userrole USING role::text::new_userrole")
        op.execute("DROP TYPE IF EXISTS userrole")
        op.execute("ALTER TYPE new_userrole RENAME TO userrole")
        
    except Exception as e:
        print(f"Note: Erreur modification users (probablement table n'existe pas encore): {e}")
        
        # Créer la table users si elle n'existe pas
        op.create_table('users',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('firebase_uid', sa.String(), nullable=False, unique=True),
            sa.Column('full_name', sa.String(), nullable=False),
            sa.Column('role', sa.Enum('admin', 'gerante', 'performer', name='userrole'), 
                     nullable=False, server_default='gerante'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'))
        )
        
        # Index sur firebase_uid
        op.create_index('ix_users_firebase_uid', 'users', ['firebase_uid'])
    
    # 2. Créer la table performers
    op.create_table('performers',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('first_name', sa.String(50), nullable=False),
        sa.Column('last_name', sa.String(50), nullable=False),
        sa.Column('email', sa.String(100), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('manager_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'))
    )
    
    # Index sur manager_id
    op.create_index('ix_performers_manager_id', 'performers', ['manager_id'])
    
    # Contrainte d'unicité
    op.create_unique_constraint(
        'unique_performer_per_manager', 
        'performers', 
        ['manager_id', 'first_name', 'last_name']
    )
    
    print("✅ Migration réussie : système d'authentification corrigé")

def downgrade():
    """
    Retour en arrière (optionnel)
    """
    # Supprimer la table performers
    op.drop_table('performers')
    
    # Restaurer l'ancien système (difficile, pas recommandé)
    print("⚠️ Downgrade : table performers supprimée")
    print("⚠️ Note : Le système de rôles reste modifié")