"""track re-enrollments after expiry

Revision ID: 2982568f4d46
Revises: 97eef399ab53
Create Date: 2026-01-31 12:23:40.626509

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2982568f4d46'
down_revision = '97eef399ab53'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # enrollment_purchases table already created in f8e3a2b1c9d0
    pass


def downgrade() -> None:
    # enrollment_purchases table dropped in f8e3a2b1c9d0
    pass
