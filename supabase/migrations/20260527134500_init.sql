-- 1. Create teams table
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    guild_id BIGINT,
    creator_id BIGINT,
    lobby_message_id BIGINT,
    textchanel_id BIGINT UNIQUE,
    voicechanel_id BIGINT UNIQUE,
    full_team BOOLEAN DEFAULT FALSE
);

-- 2. Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    discord_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL,
    email VARCHAR(255),
    is_verified BOOLEAN DEFAULT FALSE,
    role VARCHAR(50) DEFAULT 'hacker',
    resume_data JSONB,
    team_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,
    CONSTRAINT uq_user_per_guild UNIQUE (discord_id, guild_id)
);

-- 3. Create guild_settings table
CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id BIGINT PRIMARY KEY,
    ticket_support_role_id BIGINT,
    admin_role_id BIGINT,
    find_teammates_channel_id BIGINT,
    ticket_category_id BIGINT,
    ticket_panel_channel_id BIGINT,
    staff_channel_id BIGINT,
    team_category_id BIGINT,
    max_team_size INTEGER DEFAULT 4,
    mod_channel_id BIGINT,
    mod_toxicity_threshold DOUBLE PRECISION DEFAULT 0.7
);

-- 4. Create tickets table
CREATE TABLE IF NOT EXISTS tickets (
    id SERIAL PRIMARY KEY,
    guild_id BIGINT,
    user_id BIGINT,
    channel_id BIGINT UNIQUE,
    status VARCHAR(20) DEFAULT 'open',
    created_at BIGINT,
    claimed_by BIGINT,
    staff_message_id BIGINT
);

-- 5. Create infractions table
CREATE TABLE IF NOT EXISTS infractions (
    id SERIAL PRIMARY KEY,
    guild_id BIGINT,
    user_id BIGINT,
    message_content VARCHAR(2000),
    toxicity_score DOUBLE PRECISION,
    keywords JSONB,
    action_taken VARCHAR(20),
    created_at BIGINT,
    reviewed BOOLEAN DEFAULT FALSE
);

-- 6. Indexes for high performance
CREATE INDEX IF NOT EXISTS idx_users_discord_guild ON users(discord_id, guild_id);
CREATE INDEX IF NOT EXISTS idx_guild_settings_guild ON guild_settings(guild_id);
CREATE INDEX IF NOT EXISTS idx_tickets_guild_user ON tickets(guild_id, user_id);
CREATE INDEX IF NOT EXISTS idx_infractions_guild_user ON infractions(guild_id, user_id);
