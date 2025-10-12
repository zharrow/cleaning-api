"""add three tier user system

Revision ID: 005_add_three_tier_user_system
Revises: 004_add_haccp_tables
Create Date: 2025-01-11 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_add_three_tier_user_system'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==================== CREATE NEW TABLES ====================

    # 1. Create developer table
    op.create_table(
        'developer',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('firebase_uid', sa.String(255), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('firebase_uid')
    )
    op.create_index('ix_developer_email', 'developer', ['email'])
    op.create_index('ix_developer_firebase_uid', 'developer', ['firebase_uid'])

    # 2. Create admin table
    op.create_table(
        'admin',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('firebase_uid', sa.String(255), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by_id'], ['developer.id']),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('firebase_uid')
    )
    op.create_index('ix_admin_email', 'admin', ['email'])
    op.create_index('ix_admin_firebase_uid', 'admin', ['firebase_uid'])

    # 3. Create user table (employees with PIN code)
    op.create_table(
        'user',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('pin_code', sa.String(64), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('enterprise_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['enterprise_id'], ['enterprises.id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['admin.id'])
    )
    op.create_index('ix_user_email', 'user', ['email'])
    op.create_index('ix_user_enterprise_id', 'user', ['enterprise_id'])

    # 4. Create user_rooms associative table
    op.create_table(
        'user_rooms',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('room_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'room_id', name='uq_user_room')
    )
    op.create_index('ix_user_rooms_user_id', 'user_rooms', ['user_id'])
    op.create_index('ix_user_rooms_room_id', 'user_rooms', ['room_id'])

    # ==================== MODIFY ENTERPRISES TABLE ====================

    # Drop old user_id foreign key constraint
    op.drop_constraint('enterprises_user_id_fkey', 'enterprises', type_='foreignkey')

    # Add admin_id column
    op.add_column('enterprises', sa.Column('admin_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_enterprises_admin_id', 'enterprises', 'admin', ['admin_id'], ['id'])
    op.create_index('ix_enterprises_admin_id', 'enterprises', ['admin_id'])

    # Migrate data: This would require manual intervention in production
    # For now, we'll leave admin_id as nullable

    # Drop old user_id column (after data migration in production)
    # op.drop_column('enterprises', 'user_id')  # Commented out for safety

    # ==================== ADD ENTERPRISE_ID TO EXISTING TABLES ====================

    # Add enterprise_id to rooms
    op.add_column('rooms', sa.Column('enterprise_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_rooms_enterprise_id', 'rooms', 'enterprises', ['enterprise_id'], ['id'])
    op.create_index('ix_rooms_enterprise_id', 'rooms', ['enterprise_id'])

    # Add enterprise_id to task_templates
    op.add_column('task_templates', sa.Column('enterprise_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_task_templates_enterprise_id', 'task_templates', 'enterprises', ['enterprise_id'], ['id'])
    op.create_index('ix_task_templates_enterprise_id', 'task_templates', ['enterprise_id'])

    # Add enterprise_id to cleaning_sessions
    op.add_column('cleaning_sessions', sa.Column('enterprise_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_cleaning_sessions_enterprise_id', 'cleaning_sessions', 'enterprises', ['enterprise_id'], ['id'])
    op.create_index('ix_cleaning_sessions_enterprise_id', 'cleaning_sessions', ['enterprise_id'])

    # Remove unique constraint on date (now need enterprise_id + date to be unique)
    op.drop_constraint('cleaning_sessions_date_key', 'cleaning_sessions', type_='unique')
    op.create_unique_constraint('uq_cleaning_session_enterprise_date', 'cleaning_sessions', ['enterprise_id', 'date'])

    # ==================== UPDATE FOREIGN KEYS ====================

    # Update assigned_tasks.default_performer_id to reference user table
    # First, we need to drop the old constraint
    op.drop_constraint('assigned_tasks_default_performer_id_fkey', 'assigned_tasks', type_='foreignkey')

    # Add new foreign key to user table (nullable for now, will require data migration)
    op.alter_column('assigned_tasks', 'default_performer_id', nullable=True)
    op.create_foreign_key('fk_assigned_tasks_default_performer_id', 'assigned_tasks', 'user', ['default_performer_id'], ['id'])

    # Update cleaning_logs foreign keys
    # Drop old performer foreign key
    op.drop_constraint('cleaning_logs_performed_by_id_fkey', 'cleaning_logs', type_='foreignkey')

    # Add new foreign keys to user table
    op.create_foreign_key('fk_cleaning_logs_performed_by_id', 'cleaning_logs', 'user', ['performed_by_id'], ['id'])

    # recorded_by_id already references users table, update to user table
    op.drop_constraint('cleaning_logs_recorded_by_id_fkey', 'cleaning_logs', type_='foreignkey')
    op.create_foreign_key('fk_cleaning_logs_recorded_by_id', 'cleaning_logs', 'user', ['recorded_by_id'], ['id'])

    # Update HACCP tables responsible_id foreign keys (already reference users, update to user)
    haccp_tables = ['meal', 'temperature', 'cleaning_haccp', 'non_compliance', 'document']

    for table in haccp_tables:
        constraint_name = f'{table}_responsible_id_fkey'
        try:
            op.drop_constraint(constraint_name, table, type_='foreignkey')
        except:
            pass  # Constraint might not exist yet

        op.create_foreign_key(f'fk_{table}_responsible_id', table, 'user', ['responsible_id'], ['id'])


def downgrade() -> None:
    # ==================== REVERT FOREIGN KEYS ====================

    # Revert HACCP tables
    haccp_tables = ['meal', 'temperature', 'cleaning_haccp', 'non_compliance', 'document']
    for table in haccp_tables:
        op.drop_constraint(f'fk_{table}_responsible_id', table, type_='foreignkey')
        op.create_foreign_key(f'{table}_responsible_id_fkey', table, 'users', ['responsible_id'], ['id'])

    # Revert cleaning_logs
    op.drop_constraint('fk_cleaning_logs_recorded_by_id', 'cleaning_logs', type_='foreignkey')
    op.create_foreign_key('cleaning_logs_recorded_by_id_fkey', 'cleaning_logs', 'users', ['recorded_by_id'], ['id'])

    op.drop_constraint('fk_cleaning_logs_performed_by_id', 'cleaning_logs', type_='foreignkey')
    op.create_foreign_key('cleaning_logs_performed_by_id_fkey', 'cleaning_logs', 'performers', ['performed_by_id'], ['id'])

    # Revert assigned_tasks
    op.drop_constraint('fk_assigned_tasks_default_performer_id', 'assigned_tasks', type_='foreignkey')
    op.create_foreign_key('assigned_tasks_default_performer_id_fkey', 'assigned_tasks', 'performers', ['default_performer_id'], ['id'])

    # ==================== REVERT CLEANING SESSIONS ====================

    op.drop_constraint('uq_cleaning_session_enterprise_date', 'cleaning_sessions', type_='unique')
    op.create_unique_constraint('cleaning_sessions_date_key', 'cleaning_sessions', ['date'])

    op.drop_index('ix_cleaning_sessions_enterprise_id', 'cleaning_sessions')
    op.drop_constraint('fk_cleaning_sessions_enterprise_id', 'cleaning_sessions', type_='foreignkey')
    op.drop_column('cleaning_sessions', 'enterprise_id')

    # ==================== REVERT TASK TEMPLATES ====================

    op.drop_index('ix_task_templates_enterprise_id', 'task_templates')
    op.drop_constraint('fk_task_templates_enterprise_id', 'task_templates', type_='foreignkey')
    op.drop_column('task_templates', 'enterprise_id')

    # ==================== REVERT ROOMS ====================

    op.drop_index('ix_rooms_enterprise_id', 'rooms')
    op.drop_constraint('fk_rooms_enterprise_id', 'rooms', type_='foreignkey')
    op.drop_column('rooms', 'enterprise_id')

    # ==================== REVERT ENTERPRISES ====================

    # Re-add user_id column (commented out for safety)
    # op.add_column('enterprises', sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True))
    # op.create_foreign_key('enterprises_user_id_fkey', 'enterprises', 'users', ['user_id'], ['id'])

    op.drop_index('ix_enterprises_admin_id', 'enterprises')
    op.drop_constraint('fk_enterprises_admin_id', 'enterprises', type_='foreignkey')
    op.drop_column('enterprises', 'admin_id')

    # ==================== DROP NEW TABLES ====================

    op.drop_index('ix_user_rooms_room_id', 'user_rooms')
    op.drop_index('ix_user_rooms_user_id', 'user_rooms')
    op.drop_table('user_rooms')

    op.drop_index('ix_user_enterprise_id', 'user')
    op.drop_index('ix_user_email', 'user')
    op.drop_table('user')

    op.drop_index('ix_admin_firebase_uid', 'admin')
    op.drop_index('ix_admin_email', 'admin')
    op.drop_table('admin')

    op.drop_index('ix_developer_firebase_uid', 'developer')
    op.drop_index('ix_developer_email', 'developer')
    op.drop_table('developer')
