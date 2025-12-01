"""add_performance_indexes

Revision ID: 623cf76a3220
Revises: c3499087d8f4
Create Date: 2025-12-01 20:56:02.261114

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '623cf76a3220'
down_revision: Union[str, None] = 'c3499087d8f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add indexes for frequently queried columns in analytics
    
    # Users table - created_at for growth analytics
    op.create_index('ix_users_created_at', 'users', ['created_at'])
    op.create_index('ix_users_is_verified', 'users', ['is_verified'])
    
    # Enrollments table - created_at and completed_at for analytics
    op.create_index('ix_enrollments_enrolled_at', 'enrollments', ['enrolled_at'])
    
    # Payments table - status and created_at already indexed, add composite
    op.create_index('ix_payments_status_created_at', 'payments', ['status', 'created_at'])
    
    # Reviews table - created_at for recent reviews
    op.create_index('ix_reviews_created_at', 'reviews', ['created_at'])
    
    # Certificates table - issued_at for monthly stats
    op.create_index('ix_certificates_issued_at', 'certificates', ['issued_at'])
    
    # User Progress - composite index for completion queries
    op.create_index('ix_user_progress_user_completed', 'user_progress', ['user_id', 'is_completed'])


def downgrade() -> None:
    # Remove indexes in reverse order
    op.drop_index('ix_user_progress_user_completed', 'user_progress')
    op.drop_index('ix_certificates_issued_at', 'certificates')
    op.drop_index('ix_reviews_created_at', 'reviews')
    op.drop_index('ix_payments_status_created_at', 'payments')
    op.drop_index('ix_enrollments_enrolled_at', 'enrollments')
    op.drop_index('ix_users_is_verified', 'users')
    op.drop_index('ix_users_created_at', 'users')
