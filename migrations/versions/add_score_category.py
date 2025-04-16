"""add score category

Revision ID: add_score_category
Revises: 
Create Date: 2024-04-16 17:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_score_category'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add score_category column to tenant_scores table
    op.add_column('tenant_scores', sa.Column('score_category', sa.String(50), nullable=True, server_default='Yüksək riskli icarədar'))

def downgrade():
    # Remove score_category column from tenant_scores table
    op.drop_column('tenant_scores', 'score_category') 