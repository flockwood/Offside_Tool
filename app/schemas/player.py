"""
Pydantic schemas for Player API request/response validation.
"""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.models.player import PlayerPosition, PreferredFoot


# Base Schema with common attributes
class PlayerBase(BaseModel):
    """Base player schema with common attributes."""
    first_name: str = Field(..., min_length=1, max_length=100, description="Player's first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Player's last name")
    date_of_birth: Optional[date] = Field(None, description="Player's date of birth")
    nationality: Optional[str] = Field(None, max_length=100, description="Player's nationality")
    height_cm: Optional[int] = Field(None, ge=140, le=230, description="Height in centimeters")
    weight_kg: Optional[int] = Field(None, ge=40, le=150, description="Weight in kilograms")
    preferred_foot: Optional[PreferredFoot] = Field(None, description="Preferred foot")
    position: PlayerPosition = Field(..., description="Player's primary position")
    jersey_number: Optional[int] = Field(None, ge=1, le=99, description="Jersey number")
    current_club: Optional[str] = Field(None, max_length=200, description="Current club")
    market_value_euros: Optional[float] = Field(None, ge=0, description="Market value in euros")
    contract_expiry: Optional[date] = Field(None, description="Contract expiration date")
    bio: Optional[str] = Field(None, description="Player biography")
    image_url: Optional[str] = Field(None, max_length=500, description="Profile image URL")

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, v: Optional[date]) -> Optional[date]:
        """Validate that date of birth is not in the future and player is at least 10 years old."""
        if v is not None:
            today = date.today()
            if v > today:
                raise ValueError("Date of birth cannot be in the future")
            age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
            if age < 10:
                raise ValueError("Player must be at least 10 years old")
            if age > 60:
                raise ValueError("Player age cannot exceed 60 years")
        return v

    @field_validator("contract_expiry")
    @classmethod
    def validate_contract_expiry(cls, v: Optional[date]) -> Optional[date]:
        """Validate that contract expiry is not in the past."""
        if v is not None:
            if v < date.today():
                raise ValueError("Contract expiry cannot be in the past")
        return v


class PlayerCreate(PlayerBase):
    """Schema for creating a new player."""
    # Career Statistics (optional on creation, defaults to 0)
    goals: int = Field(0, ge=0, description="Total career goals")
    assists: int = Field(0, ge=0, description="Total career assists")
    matches_played: int = Field(0, ge=0, description="Total matches played")
    yellow_cards: int = Field(0, ge=0, description="Total yellow cards")
    red_cards: int = Field(0, ge=0, description="Total red cards")
    minutes_played: int = Field(0, ge=0, description="Total minutes played")
    rating: Optional[float] = Field(None, ge=0, le=10, description="Player rating (0-10)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "first_name": "Cristiano",
                "last_name": "Ronaldo",
                "date_of_birth": "1985-02-05",
                "nationality": "Portugal",
                "height_cm": 187,
                "weight_kg": 84,
                "preferred_foot": "right",
                "position": "forward",
                "jersey_number": 7,
                "current_club": "Al Nassr",
                "market_value_euros": 15000000,
                "goals": 850,
                "assists": 250,
                "matches_played": 1100,
                "rating": 8.5
            }
        }
    )


class PlayerUpdate(BaseModel):
    """Schema for updating a player (all fields optional)."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    nationality: Optional[str] = Field(None, max_length=100)
    height_cm: Optional[int] = Field(None, ge=140, le=230)
    weight_kg: Optional[int] = Field(None, ge=40, le=150)
    preferred_foot: Optional[PreferredFoot] = None
    position: Optional[PlayerPosition] = None
    jersey_number: Optional[int] = Field(None, ge=1, le=99)
    current_club: Optional[str] = Field(None, max_length=200)
    market_value_euros: Optional[float] = Field(None, ge=0)
    contract_expiry: Optional[date] = None
    goals: Optional[int] = Field(None, ge=0)
    assists: Optional[int] = Field(None, ge=0)
    matches_played: Optional[int] = Field(None, ge=0)
    yellow_cards: Optional[int] = Field(None, ge=0)
    red_cards: Optional[int] = Field(None, ge=0)
    minutes_played: Optional[int] = Field(None, ge=0)
    rating: Optional[float] = Field(None, ge=0, le=10)
    bio: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=500)

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, v: Optional[date]) -> Optional[date]:
        """Validate that date of birth is not in the future."""
        if v is not None:
            today = date.today()
            if v > today:
                raise ValueError("Date of birth cannot be in the future")
            age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
            if age < 10:
                raise ValueError("Player must be at least 10 years old")
            if age > 60:
                raise ValueError("Player age cannot exceed 60 years")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "goals": 851,
                "assists": 251,
                "matches_played": 1101,
                "current_club": "Al Nassr",
                "rating": 8.6
            }
        }
    )


class PlayerInDBBase(PlayerBase):
    """Base schema for player in database (includes ID and timestamps)."""
    id: int
    goals: int
    assists: int
    matches_played: int
    yellow_cards: int
    red_cards: int
    minutes_played: int
    rating: Optional[float]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Player(PlayerInDBBase):
    """
    Schema for player response.
    Includes computed properties.
    """
    age: Optional[int] = None
    full_name: str = ""
    goals_per_match: float = 0.0
    assists_per_match: float = 0.0

    @classmethod
    def from_orm_model(cls, db_player: "Player") -> "Player":
        """
        Create Player schema from ORM model, including computed properties.
        """
        player_dict = {
            "id": db_player.id,
            "first_name": db_player.first_name,
            "last_name": db_player.last_name,
            "date_of_birth": db_player.date_of_birth,
            "nationality": db_player.nationality,
            "height_cm": db_player.height_cm,
            "weight_kg": db_player.weight_kg,
            "preferred_foot": db_player.preferred_foot,
            "position": db_player.position,
            "jersey_number": db_player.jersey_number,
            "current_club": db_player.current_club,
            "market_value_euros": db_player.market_value_euros,
            "contract_expiry": db_player.contract_expiry,
            "goals": db_player.goals,
            "assists": db_player.assists,
            "matches_played": db_player.matches_played,
            "yellow_cards": db_player.yellow_cards,
            "red_cards": db_player.red_cards,
            "minutes_played": db_player.minutes_played,
            "rating": db_player.rating,
            "bio": db_player.bio,
            "image_url": db_player.image_url,
            "created_at": db_player.created_at,
            "updated_at": db_player.updated_at,
            "age": db_player.age,
            "full_name": db_player.full_name,
            "goals_per_match": db_player.goals_per_match,
            "assists_per_match": db_player.assists_per_match,
        }
        return cls(**player_dict)

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "first_name": "Cristiano",
                "last_name": "Ronaldo",
                "full_name": "Cristiano Ronaldo",
                "date_of_birth": "1985-02-05",
                "age": 38,
                "nationality": "Portugal",
                "height_cm": 187,
                "weight_kg": 84,
                "preferred_foot": "right",
                "position": "forward",
                "jersey_number": 7,
                "current_club": "Al Nassr",
                "market_value_euros": 15000000,
                "goals": 850,
                "assists": 250,
                "matches_played": 1100,
                "yellow_cards": 50,
                "red_cards": 5,
                "minutes_played": 95000,
                "rating": 8.5,
                "goals_per_match": 0.77,
                "assists_per_match": 0.23,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        }
    )


class PlayerList(BaseModel):
    """Schema for paginated player list response."""
    items: list[Player]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


class ComparisonMetric(BaseModel):
    """Schema for a single comparison metric."""
    player_1_value: Optional[float] = None
    player_2_value: Optional[float] = None
    winner: str  # 'player_1', 'player_2', or 'tie'

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "player_1_value": 850,
                "player_2_value": 800,
                "winner": "player_1"
            }
        }
    )


class PlayerComparisonSummary(BaseModel):
    """Schema for player comparison summary across key metrics."""
    market_value_euros: ComparisonMetric
    goals: ComparisonMetric
    assists: ComparisonMetric
    goals_per_match: ComparisonMetric
    assists_per_match: ComparisonMetric

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "market_value_euros": {
                    "player_1_value": 35000000,
                    "player_2_value": 15000000,
                    "winner": "player_1"
                },
                "goals": {
                    "player_1_value": 800,
                    "player_2_value": 850,
                    "winner": "player_2"
                },
                "assists": {
                    "player_1_value": 350,
                    "player_2_value": 250,
                    "winner": "player_1"
                },
                "goals_per_match": {
                    "player_1_value": 0.80,
                    "player_2_value": 0.77,
                    "winner": "player_1"
                },
                "assists_per_match": {
                    "player_1_value": 0.35,
                    "player_2_value": 0.23,
                    "winner": "player_1"
                }
            }
        }
    )


class PlayerComparisonResponse(BaseModel):
    """Schema for player-to-player comparison response."""
    player_1: Player
    player_2: Player
    comparison: PlayerComparisonSummary
    summary: dict[str, int]  # Count of wins for each player

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "player_1": {
                    "id": 1,
                    "first_name": "Lionel",
                    "last_name": "Messi",
                    "full_name": "Lionel Messi",
                    "position": "forward",
                    "current_club": "Inter Miami",
                    "goals": 800,
                    "assists": 350
                },
                "player_2": {
                    "id": 2,
                    "first_name": "Cristiano",
                    "last_name": "Ronaldo",
                    "full_name": "Cristiano Ronaldo",
                    "position": "forward",
                    "current_club": "Al Nassr",
                    "goals": 850,
                    "assists": 250
                },
                "comparison": {},
                "summary": {
                    "player_1_wins": 3,
                    "player_2_wins": 1,
                    "ties": 1
                }
            }
        }
    )
