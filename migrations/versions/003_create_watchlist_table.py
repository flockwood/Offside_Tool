"""create watchlist table

Revision ID: 003
Revises: 002
Create Date: 2025-01-17 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create watchlist association table for many-to-many relationship between users and players."""
    op.create_table(
        'watchlist',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'player_id')
    )

    # Create indexes for better query performance
    op.create_index(op.f('ix_watchlist_user_id'), 'watchlist', ['user_id'], unique=False)
    op.create_index(op.f('ix_watchlist_player_id'), 'watchlist', ['player_id'], unique=False)


def downgrade() -> None:
    """Drop watchlist table."""
    op.drop_index(op.f('ix_watchlist_player_id'), table_name='watchlist')
    op.drop_index(op.f('ix_watchlist_user_id'), table_name='watchlist')
    op.drop_table('watchlist')
