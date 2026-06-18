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
