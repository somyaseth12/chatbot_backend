"""Drop chat_cache table

Revision ID: ca00108ba2be
Revises: 
Create Date: 2025-07-22 18:07:56.242978

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ca00108ba2be'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
 op.drop_table('gpt_cache')
def downgrade():
    op.create_table(
        'gpt_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('query', sa.String(), nullable=True),
        sa.Column('response', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
