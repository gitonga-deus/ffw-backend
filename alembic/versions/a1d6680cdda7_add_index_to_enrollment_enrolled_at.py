"""add_index_to_enrollment_enrolled_at

Revision ID: a1d6680cdda7
Revises: c517bacf5179
Create Date: 2025-12-09 22:08:24.647452

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1d6680cdda7'
down_revision: Union[str, None] = 'c517bacf5179'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add index to enrolled_at column for faster analytics queries
    # Check if index exists first (for SQLite compatibility)
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    indexes = [idx['name'] for idx in inspector.get_indexes('enrollments')]
    
    if 'ix_enrollments_enrolled_at' not in indexes:
        op.create_index('ix_enrollments_enrolled_at', 'enrollments', ['enrolled_at'], unique=False)


def downgrade() -> None:
    # Remove index if it exists
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    indexes = [idx['name'] for idx in inspector.get_indexes('enrollments')]
    
    if 'ix_enrollments_enrolled_at' in indexes:
        op.drop_index('ix_enrollments_enrolled_at', table_name='enrollments')
