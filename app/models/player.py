"""
Player database model using SQLAlchemy 2.0.
"""
from datetime import datetime, date
from typing import Optional
from sqlalchemy import String, Integer, Float, Date, DateTime, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.db.session import Base


class PlayerPosition(str, enum.Enum):
    """Player position enumeration."""
    goalkeeper = "goalkeeper"
    defender = "defender"
    midfielder = "midfielder"
    forward = "forward"


class PreferredFoot(str, enum.Enum):
    """Preferred foot enumeration."""
    left = "left"
    right = "right"
    both = "both"


class Player(Base):
    """
    Player model representing a soccer player with comprehensive attributes.

    Attributes:
        id: Primary key
        first_name: Player's first name
        last_name: Player's last name
        date_of_birth: Player's date of birth
        nationality: Player's nationality
        position: Player's primary position
        preferred_foot: Player's preferred foot
        height_cm: Player's height in centimeters
        weight_kg: Player's weight in kilograms
        jersey_number: Player's jersey number
        current_club: Player's current club
        market_value_euros: Player's estimated market value in euros
        contract_expiry: Contract expiration date
        goals: Total career goals
        assists: Total career assists
        matches_played: Total career matches played
        yellow_cards: Total yellow cards received
        red_cards: Total red cards received
        minutes_played: Total minutes played
        rating: Average player rating (0-10 scale)
        bio: Player biography or description
        image_url: URL to player's profile image
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "players"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Personal Information
    first_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    nationality: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # Physical Attributes
    height_cm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    preferred_foot: Mapped[Optional[PreferredFoot]] = mapped_column(
        SQLEnum(PreferredFoot, name="preferred_foot_enum", create_constraint=True),
        nullable=True
    )

    # Playing Information
    position: Mapped[PlayerPosition] = mapped_column(
        SQLEnum(PlayerPosition, name="player_position_enum", create_constraint=True),
        nullable=False,
        index=True
    )
    jersey_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    current_club: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, index=True)

    # Contract & Financial
    market_value_euros: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    contract_expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Career Statistics
    goals: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    assists: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    matches_played: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    yellow_cards: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    red_cards: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    minutes_played: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Performance Rating
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Additional Information
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def __repr__(self) -> str:
        """String representation of Player."""
        return f"<Player(id={self.id}, name='{self.first_name} {self.last_name}', position={self.position})>"

    @property
    def full_name(self) -> str:
        """Get player's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self) -> Optional[int]:
        """Calculate player's age from date of birth."""
        if not self.date_of_birth:
            return None
        today = date.today()
        age = today.year - self.date_of_birth.year
        if today.month < self.date_of_birth.month or (
            today.month == self.date_of_birth.month and today.day < self.date_of_birth.day
        ):
            age -= 1
        return age

    @property
    def goals_per_match(self) -> float:
        """Calculate goals per match ratio."""
        if self.matches_played == 0:
            return 0.0
        return round(self.goals / self.matches_played, 2)

    @property
    def assists_per_match(self) -> float:
        """Calculate assists per match ratio."""
        if self.matches_played == 0:
            return 0.0
        return round(self.assists / self.matches_played, 2)
