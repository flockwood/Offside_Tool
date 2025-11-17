"""
Watchlist association table for many-to-many relationship between users and players.
"""
from sqlalchemy import Table, Column, Integer, ForeignKey
from app.db.session import Base

# Association table for the many-to-many relationship between users and players
watchlist_association = Table(
    'watchlist',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('player_id', Integer, ForeignKey('players.id', ondelete='CASCADE'), primary_key=True),
)
