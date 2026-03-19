-- Initialize bug bounty database
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create programs table
CREATE TABLE IF NOT EXISTS programs (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    name VARCHAR(255) UNIQUE NOT NULL,
    platform VARCHAR(50) NOT NULL,
    url VARCHAR(500),
    scope_domains JSON DEFAULT '[]',
    scope_excluded JSON DEFAULT '[]',
    scope_mobile_apps JSON DEFAULT '[]',
    scope_repositories JSON DEFAULT '[]',
    priority_areas JSON DEFAULT '[]',
    out_of_scope JSON DEFAULT '[]',
    severity_mapping JSON DEFAULT '{}',
    reward_tiers JSON DEFAULT '{}',
    campaigns JSON DEFAULT '[]',
    special_requirements JSON DEFAULT '{}',
    raw_policy TEXT,
    confidence_score INTEGER DEFAULT 0,
    needs_review BOOLEAN DEFAULT TRUE,
    reviewed_at TIMESTAMP,
    review_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_programs_platform ON programs(platform);
CREATE INDEX IF NOT EXISTS idx_programs_needs_review ON programs(needs_review);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO bugbounty;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO bugbounty;
