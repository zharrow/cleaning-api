"""rename title to name in task_templates

Revision ID: 002_rename_title_to_name
Revises: add_roles_001_add_admin_manager_roles
Create Date: 2025-08-29 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_rename_title_to_name'
down_revision = 'add_roles_001_add_admin_manager_roles'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename the column 'title' to 'name' in the 'task_templates' table
    op.alter_column('task_templates', 'title', new_column_name='name')


def downgrade() -> None:
    # Rename the column 'name' back to 'title' in the 'task_templates' table
    op.alter_column('task_templates', 'name', new_column_name='title')