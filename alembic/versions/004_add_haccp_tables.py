"""Add HACCP tables for kitchen management

Revision ID: 004_add_haccp_tables
Revises: 003_add_enterprise_table
Create Date: 2025-01-10 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_haccp_tables'
down_revision = '003_add_enterprise_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUMs
    sa.Enum('BABIES', 'TODDLERS', 'PRESCHOOLERS', name='section').create(op.get_bind())
    sa.Enum('BREAKFAST', 'LUNCH', 'SNACK', name='mealtype').create(op.get_bind())
    sa.Enum('RECEPTION', 'HOLDING', 'SERVICE', 'STORAGE', name='checkpoint').create(op.get_bind())
    sa.Enum('DAILY', 'WEEKLY', 'MONTHLY', name='cleaningfrequency').create(op.get_bind())
    sa.Enum('PRODUCT', 'TEMPERATURE', 'HYGIENE', 'OTHER', name='noncompliancetype').create(op.get_bind())
    sa.Enum('OPEN', 'CORRECTED', 'CLOSED', name='noncompliancestatus').create(op.get_bind())
    sa.Enum('TEMPERATURES', 'CLEANING', 'TRAINING', 'COMPLIANCE', 'OTHER', name='documentcategory').create(op.get_bind())

    # Child table
    op.create_table('child',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('enterprise_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('birth_date', sa.Date(), nullable=False),
        sa.Column('section', sa.Enum('BABIES', 'TODDLERS', 'PRESCHOOLERS', name='section'), nullable=False),
        sa.Column('allergies', sa.Text(), nullable=True, comment='Known allergies (comma-separated)'),
        sa.Column('specific_diet', sa.Text(), nullable=True, comment='Special diet requirements'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.ForeignKeyConstraint(['enterprise_id'], ['enterprises.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id')
    )
    op.create_index(op.f('ix_child_enterprise_id'), 'child', ['enterprise_id'], unique=False)

    # Supplier table
    op.create_table('supplier',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('enterprise_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('contact_name', sa.String(length=150), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=150), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('haccp_certified', sa.Boolean(), nullable=False, default=False, comment='HACCP compliant supplier'),
        sa.Column('validation_date', sa.Date(), nullable=True, comment='Last verification date'),
        sa.ForeignKeyConstraint(['enterprise_id'], ['enterprises.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id')
    )
    op.create_index(op.f('ix_supplier_enterprise_id'), 'supplier', ['enterprise_id'], unique=False)

    # Product table
    op.create_table('product',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('enterprise_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True, comment='Category (meat, dairy, vegetable, etc.)'),
        sa.Column('allergens', sa.Text(), nullable=True, comment='List of allergens (comma-separated)'),
        sa.Column('stock_unit', sa.String(length=20), nullable=True, comment='Unit (kg, L, etc.)'),
        sa.Column('current_stock', sa.DECIMAL(precision=10, scale=2), nullable=True, comment='Quantity in stock'),
        sa.Column('expiry_date', sa.Date(), nullable=True, comment='Expiry date'),
        sa.ForeignKeyConstraint(['enterprise_id'], ['enterprises.id'], ),
        sa.ForeignKeyConstraint(['supplier_id'], ['supplier.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id')
    )
    op.create_index(op.f('ix_product_enterprise_id'), 'product', ['enterprise_id'], unique=False)

    # Batch table
    op.create_table('batch',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('batch_code', sa.String(length=100), nullable=False, comment='Batch reference'),
        sa.Column('reception_date', sa.Date(), nullable=False),
        sa.Column('received_quantity', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('reception_temperature', sa.DECIMAL(precision=5, scale=2), nullable=True, comment='Temperature at reception (°C)'),
        sa.Column('is_compliant', sa.Boolean(), nullable=False, default=True, comment='Compliant at reception'),
        sa.Column('observations', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['product.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id')
    )

    # Meal table
    op.create_table('meal',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('enterprise_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('responsible_id', postgresql.UUID(as_uuid=True), nullable=True, comment='User who validated the meal'),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('meal_type', sa.Enum('BREAKFAST', 'LUNCH', 'SNACK', name='mealtype'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True, comment='Meal details (menu, ingredients)'),
        sa.ForeignKeyConstraint(['enterprise_id'], ['enterprises.id'], ),
        sa.ForeignKeyConstraint(['supplier_id'], ['supplier.id'], ),
        sa.ForeignKeyConstraint(['batch_id'], ['batch.id'], ),
        sa.ForeignKeyConstraint(['responsible_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id')
    )
    op.create_index(op.f('ix_meal_enterprise_id'), 'meal', ['enterprise_id'], unique=False)
    op.create_index(op.f('ix_meal_date'), 'meal', ['date'], unique=False)

    # Temperature table
    op.create_table('temperature',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('meal_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('responsible_id', postgresql.UUID(as_uuid=True), nullable=True, comment='User who recorded temperature'),
        sa.Column('checkpoint', sa.Enum('RECEPTION', 'HOLDING', 'SERVICE', 'STORAGE', name='checkpoint'), nullable=False, comment='Control stage'),
        sa.Column('temperature', sa.DECIMAL(precision=5, scale=2), nullable=False, comment='Measured temperature (°C)'),
        sa.Column('is_compliant', sa.Boolean(), nullable=False, default=True),
        sa.Column('observations', sa.Text(), nullable=True),
        sa.Column('control_date', sa.DateTime(timezone=True), nullable=False, comment='Date/time of reading'),
        sa.ForeignKeyConstraint(['meal_id'], ['meal.id'], ),
        sa.ForeignKeyConstraint(['responsible_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id')
    )
    op.create_index(op.f('ix_temperature_meal_id'), 'temperature', ['meal_id'], unique=False)

    # Equipment table
    op.create_table('equipment',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('enterprise_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=True, comment='Category (fridge, oven, warmer, etc.)'),
        sa.Column('last_control_date', sa.Date(), nullable=True),
        sa.Column('target_temperature', sa.DECIMAL(precision=5, scale=2), nullable=True, comment='Target temperature for fridges/freezers'),
        sa.Column('is_compliant', sa.Boolean(), nullable=False, default=True),
        sa.Column('observations', sa.Text(), nullable=True, comment='Maintenance details'),
        sa.ForeignKeyConstraint(['enterprise_id'], ['enterprises.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id')
    )
    op.create_index(op.f('ix_equipment_enterprise_id'), 'equipment', ['enterprise_id'], unique=False)

    # Cleaning HACCP table
    op.create_table('cleaning_haccp',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('enterprise_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('responsible_id', postgresql.UUID(as_uuid=True), nullable=True, comment='User who performed cleaning'),
        sa.Column('zone', sa.String(length=100), nullable=False, comment='Cleaned area (kitchen, refrigerator, floor, etc.)'),
        sa.Column('product_used', sa.String(length=100), nullable=True, comment='Disinfectant or detergent used'),
        sa.Column('frequency', sa.Enum('DAILY', 'WEEKLY', 'MONTHLY', name='cleaningfrequency'), nullable=False),
        sa.Column('cleaning_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('observations', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['enterprise_id'], ['enterprises.id'], ),
        sa.ForeignKeyConstraint(['responsible_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id')
    )
    op.create_index(op.f('ix_cleaning_haccp_enterprise_id'), 'cleaning_haccp', ['enterprise_id'], unique=False)

    # Non-compliance table
    op.create_table('non_compliance',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('enterprise_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('responsible_id', postgresql.UUID(as_uuid=True), nullable=True, comment='User responsible for incident'),
        sa.Column('type', sa.Enum('PRODUCT', 'TEMPERATURE', 'HYGIENE', 'OTHER', name='noncompliancetype'), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, comment='Non-compliance details'),
        sa.Column('report_date', sa.DateTime(timezone=True), nullable=False, comment='Incident date'),
        sa.Column('corrective_action', sa.Text(), nullable=True, comment='Corrective measure taken'),
        sa.Column('status', sa.Enum('OPEN', 'CORRECTED', 'CLOSED', name='noncompliancestatus'), nullable=False, default='OPEN'),
        sa.ForeignKeyConstraint(['enterprise_id'], ['enterprises.id'], ),
        sa.ForeignKeyConstraint(['responsible_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id')
    )
    op.create_index(op.f('ix_non_compliance_enterprise_id'), 'non_compliance', ['enterprise_id'], unique=False)

    # Document table
    op.create_table('document',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('enterprise_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('responsible_id', postgresql.UUID(as_uuid=True), nullable=True, comment='User who uploaded document'),
        sa.Column('name', sa.String(length=150), nullable=False, comment='Document name'),
        sa.Column('category', sa.Enum('TEMPERATURES', 'CLEANING', 'TRAINING', 'COMPLIANCE', 'OTHER', name='documentcategory'), nullable=False),
        sa.Column('file_path', sa.String(length=255), nullable=False, comment='Link to file (PDF, image, etc.)'),
        sa.Column('creation_date', sa.Date(), nullable=False),
        sa.Column('retention_period', sa.String(length=50), nullable=True, comment="Retention period (e.g. '5 years')"),
        sa.ForeignKeyConstraint(['enterprise_id'], ['enterprises.id'], ),
        sa.ForeignKeyConstraint(['responsible_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id')
    )
    op.create_index(op.f('ix_document_enterprise_id'), 'document', ['enterprise_id'], unique=False)

    # Meal Children associative table
    op.create_table('meal_children',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('meal_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('child_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('portion', sa.String(length=50), nullable=True, comment="Portion served (e.g. '1/2', 'full', 'small')"),
        sa.Column('observations', sa.Text(), nullable=True, comment='Notes (refusal, appetite, incident)'),
        sa.ForeignKeyConstraint(['meal_id'], ['meal.id'], ),
        sa.ForeignKeyConstraint(['child_id'], ['child.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id')
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('meal_children')
    op.drop_index(op.f('ix_document_enterprise_id'), table_name='document')
    op.drop_table('document')
    op.drop_index(op.f('ix_non_compliance_enterprise_id'), table_name='non_compliance')
    op.drop_table('non_compliance')
    op.drop_index(op.f('ix_cleaning_haccp_enterprise_id'), table_name='cleaning_haccp')
    op.drop_table('cleaning_haccp')
    op.drop_index(op.f('ix_equipment_enterprise_id'), table_name='equipment')
    op.drop_table('equipment')
    op.drop_index(op.f('ix_temperature_meal_id'), table_name='temperature')
    op.drop_table('temperature')
    op.drop_index(op.f('ix_meal_date'), table_name='meal')
    op.drop_index(op.f('ix_meal_enterprise_id'), table_name='meal')
    op.drop_table('meal')
    op.drop_table('batch')
    op.drop_index(op.f('ix_product_enterprise_id'), table_name='product')
    op.drop_table('product')
    op.drop_index(op.f('ix_supplier_enterprise_id'), table_name='supplier')
    op.drop_table('supplier')
    op.drop_index(op.f('ix_child_enterprise_id'), table_name='child')
    op.drop_table('child')

    # Drop ENUMs
    sa.Enum('TEMPERATURES', 'CLEANING', 'TRAINING', 'COMPLIANCE', 'OTHER', name='documentcategory').drop(op.get_bind())
    sa.Enum('OPEN', 'CORRECTED', 'CLOSED', name='noncompliancestatus').drop(op.get_bind())
    sa.Enum('PRODUCT', 'TEMPERATURE', 'HYGIENE', 'OTHER', name='noncompliancetype').drop(op.get_bind())
    sa.Enum('DAILY', 'WEEKLY', 'MONTHLY', name='cleaningfrequency').drop(op.get_bind())
    sa.Enum('RECEPTION', 'HOLDING', 'SERVICE', 'STORAGE', name='checkpoint').drop(op.get_bind())
    sa.Enum('BREAKFAST', 'LUNCH', 'SNACK', name='mealtype').drop(op.get_bind())
    sa.Enum('BABIES', 'TODDLERS', 'PRESCHOOLERS', name='section').drop(op.get_bind())
