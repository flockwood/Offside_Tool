"""Initial migration - Create players table

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create players table with all fields and constraints."""
    # Note: ENUM types are already created in the database
    # Create players table
    op.create_table(
        'players',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('nationality', sa.String(length=100), nullable=True),
        sa.Column('height_cm', sa.Integer(), nullable=True),
        sa.Column('weight_kg', sa.Integer(), nullable=True),
        sa.Column('preferred_foot', sa.Enum('left', 'right', 'both',
                                           name='preferred_foot_enum',
                                           create_type=False), nullable=True),
        sa.Column('position', sa.Enum('goalkeeper', 'defender', 'midfielder', 'forward',
                                      name='player_position_enum',
                                      create_type=False), nullable=False),
        sa.Column('jersey_number', sa.Integer(), nullable=True),
        sa.Column('current_club', sa.String(length=200), nullable=True),
        sa.Column('market_value_euros', sa.Float(), nullable=True),
        sa.Column('contract_expiry', sa.Date(), nullable=True),
        sa.Column('goals', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('assists', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('matches_played', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('yellow_cards', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('red_cards', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('minutes_played', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for better query performance
    op.create_index(op.f('ix_players_id'), 'players', ['id'], unique=False)
    op.create_index(op.f('ix_players_first_name'), 'players', ['first_name'], unique=False)
    op.create_index(op.f('ix_players_last_name'), 'players', ['last_name'], unique=False)
    op.create_index(op.f('ix_players_nationality'), 'players', ['nationality'], unique=False)
    op.create_index(op.f('ix_players_position'), 'players', ['position'], unique=False)
    op.create_index(op.f('ix_players_current_club'), 'players', ['current_club'], unique=False)

    # Create trigger to automatically update updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    op.execute("""
        CREATE TRIGGER update_players_updated_at
        BEFORE UPDATE ON players
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Drop players table and associated types."""
    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS update_players_updated_at ON players")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

    # Drop indexes
    op.drop_index(op.f('ix_players_current_club'), table_name='players')
    op.drop_index(op.f('ix_players_position'), table_name='players')
    op.drop_index(op.f('ix_players_nationality'), table_name='players')
    op.drop_index(op.f('ix_players_last_name'), table_name='players')
    op.drop_index(op.f('ix_players_first_name'), table_name='players')
    op.drop_index(op.f('ix_players_id'), table_name='players')

    # Drop table
    op.drop_table('players')

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS player_position_enum")
    op.execute("DROP TYPE IF EXISTS preferred_foot_enum")
