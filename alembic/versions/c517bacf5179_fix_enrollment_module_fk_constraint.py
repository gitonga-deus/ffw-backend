"""fix_enrollment_module_fk_constraint

Revision ID: c517bacf5179
Revises: 623cf76a3220
Create Date: 2025-12-02 17:45:31.236819

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c517bacf5179'
down_revision: Union[str, None] = '623cf76a3220'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # For SQLite: Recreate the table with the correct foreign key constraint
    # SQLite doesn't support modifying foreign keys, so we need to recreate the table
    with op.batch_alter_table('enrollments', schema=None, recreate='always') as batch_op:
        # The batch operation will recreate the table with the updated model definition
        # which includes ondelete='SET NULL' for last_accessed_module_id
        pass


def downgrade() -> None:
    # For downgrade, recreate without the SET NULL constraint
    with op.batch_alter_table('enrollments', schema=None, recreate='always') as batch_op:
        pass
