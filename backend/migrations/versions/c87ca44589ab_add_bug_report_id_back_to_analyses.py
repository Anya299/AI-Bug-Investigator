"""add bug_report_id back to analyses

Revision ID: c87ca44589ab
Revises: 5a1d7d7485ac
Create Date: 2026-08-01 19:41:10.838476

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c87ca44589ab'
down_revision: Union[str, Sequence[str], None] = '5a1d7d7485ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('bug_reports',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('stack_trace', sa.Text(), nullable=True),
    sa.Column('logs', sa.Text(), nullable=True),
    sa.Column('language', sa.String(length=100), nullable=True),
    sa.Column('framework', sa.String(length=100), nullable=True),
    sa.Column('severity', sa.String(length=50), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bug_reports_id'), 'bug_reports', ['id'], unique=False)
    op.add_column('analyses', sa.Column('bug_report_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_analyses_bug_report_id', 'analyses', 'bug_reports', ['bug_report_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_analyses_bug_report_id', 'analyses', type_='foreignkey')
    op.drop_column('analyses', 'bug_report_id')
    op.drop_index(op.f('ix_bug_reports_id'), table_name='bug_reports')
    op.drop_table('bug_reports')