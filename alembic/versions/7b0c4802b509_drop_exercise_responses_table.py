"""drop_exercise_responses_table

Revision ID: 7b0c4802b509
Revises: f8f50d33cf38
Create Date: 2025-11-22 19:16:51.259585

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b0c4802b509'
down_revision: Union[str, None] = 'f8f50d33cf38'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the exercise_responses table
    op.drop_index(op.f('ix_exercise_responses_user_id'), table_name='exercise_responses')
    op.drop_index(op.f('ix_exercise_responses_content_id'), table_name='exercise_responses')
    op.drop_table('exercise_responses')


def downgrade() -> None:
    # Recreate the exercise_responses table if needed
    op.create_table('exercise_responses',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('content_id', sa.String(), nullable=False),
    sa.Column('exercise_id', sa.String(length=255), nullable=False),
    sa.Column('response_data', sa.String(), nullable=False),
    sa.Column('submitted_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['content_id'], ['content.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'content_id', 'exercise_id', name='uq_exercise_response')
    )
    op.create_index(op.f('ix_exercise_responses_content_id'), 'exercise_responses', ['content_id'], unique=False)
    op.create_index(op.f('ix_exercise_responses_user_id'), 'exercise_responses', ['user_id'], unique=False)
