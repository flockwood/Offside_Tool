-- Create ENUM types
CREATE TYPE player_position_enum AS ENUM ('goalkeeper', 'defender', 'midfielder', 'forward');
CREATE TYPE preferred_foot_enum AS ENUM ('left', 'right', 'both');

-- Create players table
CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    nationality VARCHAR(100),
    height_cm INTEGER,
    weight_kg INTEGER,
    preferred_foot preferred_foot_enum,
    position player_position_enum NOT NULL,
    jersey_number INTEGER,
    current_club VARCHAR(200),
    market_value_euros FLOAT,
    contract_expiry DATE,
    goals INTEGER NOT NULL DEFAULT 0,
    assists INTEGER NOT NULL DEFAULT 0,
    matches_played INTEGER NOT NULL DEFAULT 0,
    yellow_cards INTEGER NOT NULL DEFAULT 0,
    red_cards INTEGER NOT NULL DEFAULT 0,
    minutes_played INTEGER NOT NULL DEFAULT 0,
    rating FLOAT,
    bio TEXT,
    image_url VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE INDEX ix_players_id ON players(id);
CREATE INDEX ix_players_first_name ON players(first_name);
CREATE INDEX ix_players_last_name ON players(last_name);
CREATE INDEX ix_players_nationality ON players(nationality);
CREATE INDEX ix_players_position ON players(position);
CREATE INDEX ix_players_current_club ON players(current_club);

-- Create update trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
CREATE TRIGGER update_players_updated_at
    BEFORE UPDATE ON players
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create Alembic version table and mark as migrated
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

INSERT INTO alembic_version (version_num) VALUES ('001');
