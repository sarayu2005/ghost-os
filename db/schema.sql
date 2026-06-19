-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Beliefs table (e.g., "Open source is important", "AGI safety matters")
CREATE TABLE IF NOT EXISTS beliefs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    belief_text TEXT NOT NULL,
    category VARCHAR(100),
    strength FLOAT DEFAULT 0.7,  -- How strongly user believes (0.0-1.0)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- News stories cache
CREATE TABLE IF NOT EXISTS news_stories (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    url TEXT UNIQUE,
    source VARCHAR(255),
    relevance_score FLOAT,
    novelty_score FLOAT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Belief-to-news matches (which beliefs match which news)
CREATE TABLE IF NOT EXISTS belief_matches (
    id SERIAL PRIMARY KEY,
    news_id INTEGER NOT NULL REFERENCES news_stories(id),
    belief_id INTEGER NOT NULL REFERENCES beliefs(id),
    match_score FLOAT,  -- How well does this news match this belief (0.0-1.0)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_beliefs_user ON beliefs(user_id);
CREATE INDEX IF NOT EXISTS idx_belief_matches_news ON belief_matches(news_id);
CREATE INDEX IF NOT EXISTS idx_belief_matches_belief ON belief_matches(belief_id);

-- Add persona table
CREATE TABLE IF NOT EXISTS user_personas (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
    full_name VARCHAR(255),
    title VARCHAR(255),  -- e.g., "AI Safety Researcher"
    industry VARCHAR(255),  -- e.g., "Technology"
    audience VARCHAR(255),  -- e.g., "AI professionals, policymakers"
    tone VARCHAR(255),  -- e.g., "thoughtful, formal, conversational"
    expertise_areas TEXT,  -- Comma-separated
    years_experience INTEGER,
    company VARCHAR(255),
    website VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pending content awaiting HITL approval
CREATE TABLE IF NOT EXISTS pending_content (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    news_id INTEGER REFERENCES news_stories(id),
    news_title TEXT,
    news_content TEXT,
    content_type VARCHAR(50),  -- 'linkedin', 'twitter', 'substack'
    generated_text TEXT,
    quality_score FLOAT,
    edited BOOLEAN DEFAULT false,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, approved, rejected, published
    scheduled_for TIMESTAMP,
    approved_at TIMESTAMP,
    published_at TIMESTAMP,
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pending_user ON pending_content(user_id);
CREATE INDEX idx_pending_status ON pending_content(status);

-- Columns added post-initial-schema (safe to run on existing DBs)
ALTER TABLE beliefs ADD COLUMN IF NOT EXISTS counter_argument TEXT;

ALTER TABLE users ADD COLUMN IF NOT EXISTS linkedin_access_token TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS linkedin_person_urn TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS linkedin_token_expiry TIMESTAMP;

ALTER TABLE pending_content ADD COLUMN IF NOT EXISTS conviction_score FLOAT;
ALTER TABLE pending_content ADD COLUMN IF NOT EXISTS matched_beliefs_json JSONB;
