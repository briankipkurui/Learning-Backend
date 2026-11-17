"""remove_packages_add_enrollment_expiry

Revision ID: f8e3a2b1c9d0
Revises: 2d8f5002fb9d
Create Date: 2025-01-13

This migration:
1. Adds expires_at column to enrollments table
2. Creates enrollment_purchases table to track purchase history
3. Drops all CV analysis and interview practice package/purchase/balance tables
   since features are now unlimited with active enrollment

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# Helper function to check if table exists
def table_exists(table_name):
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()

# revision identifiers, used by Alembic.
revision = 'f8e3a2b1c9d0'
down_revision = '2d8f5002fb9d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add expires_at column to enrollments
    op.add_column('enrollments', sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True))
    
    # Create enrollment_purchases table for purchase audit trail
    op.create_table('enrollment_purchases',
        sa.Column('enrollment_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False, comment='Amount paid in cents'),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('payment_reference', sa.String(length=255), nullable=True, comment='Stripe payment intent ID'),
        sa.Column('purchased_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_renewal', sa.Boolean(), nullable=True, default=False, comment='True if this is a renewal purchase'),
        sa.Column('Id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['enrollment_id'], ['enrollments.Id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.Id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('Id')
    )
    op.create_index(op.f('ix_enrollment_purchases_Id'), 'enrollment_purchases', ['Id'], unique=False)
    op.create_index(op.f('ix_enrollment_purchases_enrollment_id'), 'enrollment_purchases', ['enrollment_id'], unique=False)
    op.create_index(op.f('ix_enrollment_purchases_user_id'), 'enrollment_purchases', ['user_id'], unique=False)
    
    # Drop CV analysis packages, purchases, and balances tables (if they exist)
    # These tables may not exist in all environments
    if table_exists('cv_analysis_purchases'):
        op.drop_index(op.f('ix_cv_analysis_purchases_user_id'), table_name='cv_analysis_purchases')
        op.drop_index(op.f('ix_cv_analysis_purchases_Id'), table_name='cv_analysis_purchases')
        op.drop_table('cv_analysis_purchases')
    
    if table_exists('cv_analysis_balances'):
        op.drop_index(op.f('ix_cv_analysis_balances_user_id'), table_name='cv_analysis_balances')
        op.drop_index(op.f('ix_cv_analysis_balances_Id'), table_name='cv_analysis_balances')
        op.drop_table('cv_analysis_balances')
    
    if table_exists('cv_analysis_packages'):
        op.drop_index(op.f('ix_cv_analysis_packages_Id'), table_name='cv_analysis_packages')
        op.drop_table('cv_analysis_packages')
    
    # Drop interview practice packages, purchases, and balances tables (if they exist)
    if table_exists('interview_practice_purchases'):
        op.drop_index(op.f('ix_interview_practice_purchases_user_id'), table_name='interview_practice_purchases')
        op.drop_index(op.f('ix_interview_practice_purchases_Id'), table_name='interview_practice_purchases')
        op.drop_table('interview_practice_purchases')
    
    if table_exists('interview_practice_balances'):
        op.drop_index(op.f('ix_interview_practice_balances_user_id'), table_name='interview_practice_balances')
        op.drop_index(op.f('ix_interview_practice_balances_Id'), table_name='interview_practice_balances')
        op.drop_table('interview_practice_balances')
    
    if table_exists('interview_practice_packages'):
        op.drop_index(op.f('ix_interview_practice_packages_Id'), table_name='interview_practice_packages')
        op.drop_table('interview_practice_packages')


def downgrade() -> None:
    # Recreate CV analysis packages table
    op.create_table('cv_analysis_packages',
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('credits', sa.Integer(), nullable=False),
        sa.Column('price', sa.Integer(), nullable=False, comment='Price in cents'),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_addon', sa.Boolean(), nullable=True),
        sa.Column('addon_price', sa.Integer(), nullable=True),
        sa.Column('Id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('Id')
    )
    op.create_index(op.f('ix_cv_analysis_packages_Id'), 'cv_analysis_packages', ['Id'], unique=False)
    
    # Recreate CV analysis balances table
    op.create_table('cv_analysis_balances',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('available_credits', sa.Integer(), nullable=False),
        sa.Column('Id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.Id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('Id')
    )
    op.create_index(op.f('ix_cv_analysis_balances_Id'), 'cv_analysis_balances', ['Id'], unique=False)
    op.create_index(op.f('ix_cv_analysis_balances_user_id'), 'cv_analysis_balances', ['user_id'], unique=True)
    
    # Recreate CV analysis purchases table
    op.create_table('cv_analysis_purchases',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('package_id', sa.UUID(), nullable=False),
        sa.Column('credits_purchased', sa.Integer(), nullable=False),
        sa.Column('amount_paid', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('payment_reference', sa.String(length=255), nullable=True),
        sa.Column('is_addon_purchase', sa.Boolean(), nullable=True),
        sa.Column('Id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['package_id'], ['cv_analysis_packages.Id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['user_id'], ['users.Id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('Id')
    )
    op.create_index(op.f('ix_cv_analysis_purchases_Id'), 'cv_analysis_purchases', ['Id'], unique=False)
    op.create_index(op.f('ix_cv_analysis_purchases_user_id'), 'cv_analysis_purchases', ['user_id'], unique=False)
    
    # Recreate interview practice packages table
    op.create_table('interview_practice_packages',
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('credits', sa.Integer(), nullable=False),
        sa.Column('price', sa.Integer(), nullable=False, comment='Price in cents'),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_addon', sa.Boolean(), nullable=True),
        sa.Column('addon_price', sa.Integer(), nullable=True),
        sa.Column('Id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('Id')
    )
    op.create_index(op.f('ix_interview_practice_packages_Id'), 'interview_practice_packages', ['Id'], unique=False)
    
    # Recreate interview practice balances table
    op.create_table('interview_practice_balances',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('available_credits', sa.Integer(), nullable=False),
        sa.Column('Id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.Id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('Id')
    )
    op.create_index(op.f('ix_interview_practice_balances_Id'), 'interview_practice_balances', ['Id'], unique=False)
    op.create_index(op.f('ix_interview_practice_balances_user_id'), 'interview_practice_balances', ['user_id'], unique=True)
    
    # Recreate interview practice purchases table
    op.create_table('interview_practice_purchases',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('package_id', sa.UUID(), nullable=False),
        sa.Column('credits_purchased', sa.Integer(), nullable=False),
        sa.Column('amount_paid', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('payment_reference', sa.String(length=255), nullable=True),
        sa.Column('enrollment_id', sa.UUID(), nullable=True),
        sa.Column('Id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['enrollment_id'], ['enrollments.Id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['package_id'], ['interview_practice_packages.Id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['user_id'], ['users.Id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('Id')
    )
    op.create_index(op.f('ix_interview_practice_purchases_Id'), 'interview_practice_purchases', ['Id'], unique=False)
    op.create_index(op.f('ix_interview_practice_purchases_user_id'), 'interview_practice_purchases', ['user_id'], unique=False)
    
    # Drop enrollment_purchases table
    op.drop_index(op.f('ix_enrollment_purchases_user_id'), table_name='enrollment_purchases')
    op.drop_index(op.f('ix_enrollment_purchases_enrollment_id'), table_name='enrollment_purchases')
    op.drop_index(op.f('ix_enrollment_purchases_Id'), table_name='enrollment_purchases')
    op.drop_table('enrollment_purchases')
    
    # Remove expires_at from enrollments
    op.drop_column('enrollments', 'expires_at')
