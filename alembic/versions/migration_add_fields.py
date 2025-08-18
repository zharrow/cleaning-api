"""add missing fields for nettoya

Revision ID: add_missing_fields_001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'add_missing_fields_001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Ajouter created_by_id à performers
    op.add_column('performers', 
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        'fk_performers_created_by',
        'performers', 'users',
        ['created_by_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Ajouter image_key à rooms
    op.add_column('rooms',
        sa.Column('image_key', sa.String(255), nullable=True)
    )
    
    # Ajouter les nouveaux champs à task_templates
    op.add_column('task_templates',
        sa.Column('title', sa.String(200), nullable=True)
    )
    op.add_column('task_templates',
        sa.Column('default_duration', sa.Integer(), server_default='15', nullable=False)
    )
    op.add_column('task_templates',
        sa.Column('type', sa.String(50), server_default='daily', nullable=False)
    )
    
    # Migrer name vers title si nécessaire
    op.execute("UPDATE task_templates SET title = name WHERE title IS NULL")
    op.alter_column('task_templates', 'title', nullable=False)
    
    # Ajouter frequency JSON à assigned_tasks
    op.add_column('assigned_tasks',
        sa.Column('frequency', sa.JSON(), nullable=True)
    )
    
    # Migrer les anciennes données vers le nouveau format
    op.execute("""
        UPDATE assigned_tasks 
        SET frequency = jsonb_build_object(
            'type', CASE 
                WHEN frequency_days = 1 THEN 'daily'
                WHEN frequency_days = 7 THEN 'weekly'
                ELSE 'monthly'
            END,
            'times_per_day', COALESCE(times_per_day, 1),
            'days', '[]'::jsonb
        )
        WHERE frequency IS NULL
    """)
    
    op.add_column('assigned_tasks',
        sa.Column('expected_duration', sa.Integer(), server_default='15', nullable=False)
    )
    op.add_column('assigned_tasks',
        sa.Column('order_in_room', sa.Integer(), server_default='0', nullable=False)
    )
    
    # Ajouter les champs à cleaning_logs
    op.add_column('cleaning_logs',
        sa.Column('recorded_by_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column('cleaning_logs',
        sa.Column('performed_at', sa.DateTime(), nullable=True)
    )
    op.add_column('cleaning_logs',
        sa.Column('photo_urls', sa.JSON(), nullable=True)
    )
    op.add_column('cleaning_logs',
        sa.Column('note', sa.Text(), nullable=True)
    )
    
    # Migrer les anciennes données
    op.execute("UPDATE cleaning_logs SET performed_at = COALESCE(timestamp, created_at) WHERE performed_at IS NULL")
    op.execute("UPDATE cleaning_logs SET photo_urls = photos::jsonb WHERE photos IS NOT NULL AND photo_urls IS NULL")
    op.execute("UPDATE cleaning_logs SET note = notes WHERE notes IS NOT NULL AND note IS NULL")
    
    op.create_foreign_key(
        'fk_cleaning_logs_recorded_by',
        'cleaning_logs', 'users',
        ['recorded_by_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Modifier la table exports
    op.execute("""
        ALTER TABLE exports 
        ADD COLUMN IF NOT EXISTS pdf_url VARCHAR(500),
        ADD COLUMN IF NOT EXISTS zip_url VARCHAR(500),
        ADD COLUMN IF NOT EXISTS exported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """)
    
    # Créer les index pour les performances
    op.create_index('ix_cleaning_sessions_date', 'cleaning_sessions', ['date'])
    op.create_index('ix_cleaning_logs_session_performed', 'cleaning_logs', ['session_id', 'performed_by_id'])
    op.create_index('ix_assigned_tasks_room_order', 'assigned_tasks', ['room_id', 'order_in_room'])

def downgrade():
    # Supprimer les index
    op.drop_index('ix_assigned_tasks_room_order')
    op.drop_index('ix_cleaning_logs_session_performed')
    op.drop_index('ix_cleaning_sessions_date')
    
    # Restaurer les colonnes originales
    op.drop_constraint('fk_cleaning_logs_recorded_by', 'cleaning_logs')
    op.drop_column('cleaning_logs', 'recorded_by_id')
    op.drop_column('cleaning_logs', 'performed_at')
    op.drop_column('cleaning_logs', 'photo_urls')
    op.drop_column('cleaning_logs', 'note')
    
    op.drop_column('assigned_tasks', 'frequency')
    op.drop_column('assigned_tasks', 'expected_duration')
    op.drop_column('assigned_tasks', 'order_in_room')
    
    op.drop_column('task_templates', 'title')
    op.drop_column('task_templates', 'default_duration')
    op.drop_column('task_templates', 'type')
    
    op.drop_column('rooms', 'image_key')
    
    op.drop_constraint('fk_performers_created_by', 'performers')
    op.drop_column('performers', 'created_by_id')