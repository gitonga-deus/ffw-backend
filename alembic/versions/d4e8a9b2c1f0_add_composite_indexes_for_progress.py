"""add_composite_indexes_for_progress

Revision ID: d4e8a9b2c1f0
Revises: a1d6680cdda7
Create Date: 2025-12-10 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e8a9b2c1f0'
down_revision: Union[str, None] = 'a1d6680cdda7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add composite index for content table to optimize sequential access queries
    # This supports queries like: SELECT * FROM content WHERE module_id = ? ORDER BY order_index
    op.create_index('ix_content_module_order', 'content', ['module_id', 'order_index'])
    
    # Add composite index for modules table to optimize module ordering queries
    # This supports queries like: SELECT * FROM modules WHERE course_id = ? ORDER BY order_index
    op.create_index('ix_modules_course_order', 'modules', ['course_id', 'order_index'])


def downgrade() -> None:
    # Remove indexes in reverse order
    op.drop_index('ix_modules_course_order', 'modules')
    op.drop_index('ix_content_module_order', 'content')
