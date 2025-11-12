-- Supabase Schema for Investor Sentiment Tracker
-- Run this in Supabase SQL Editor: https://app.supabase.com/project/_/sql

-- Articles table: stores raw news articles
CREATE TABLE IF NOT EXISTS articles (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    published_at TIMESTAMPTZ NOT NULL,
    content_snippet TEXT,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for faster date range queries
CREATE INDEX IF NOT EXISTS idx_articles_published
ON articles(published_at DESC);

-- Index for URL lookups (deduplication)
CREATE INDEX IF NOT EXISTS idx_articles_url
ON articles(url);


-- Mentions table: sentiment analysis results
CREATE TABLE IF NOT EXISTS mentions (
    id BIGSERIAL PRIMARY KEY,
    article_id BIGINT NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    company_ticker TEXT NOT NULL,
    sentiment_score REAL NOT NULL CHECK (sentiment_score >= -1.0 AND sentiment_score <= 1.0),
    sentiment_label TEXT NOT NULL CHECK (sentiment_label IN ('negative', 'neutral', 'positive')),
    key_topics JSONB DEFAULT '[]'::jsonb,
    analyzed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for ticker + date queries
CREATE INDEX IF NOT EXISTS idx_mentions_ticker
ON mentions(company_ticker);

CREATE INDEX IF NOT EXISTS idx_mentions_article
ON mentions(article_id);


-- Daily aggregates table: pre-computed summaries
CREATE TABLE IF NOT EXISTS daily_agg (
    date DATE NOT NULL,
    ticker TEXT NOT NULL,
    avg_sentiment REAL NOT NULL,
    article_count INTEGER NOT NULL,
    sentiment_trend TEXT CHECK (sentiment_trend IN ('improving', 'stable', 'declining')),
    top_topics JSONB DEFAULT '[]'::jsonb,
    ir_brief TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (date, ticker)
);

-- Index for date range queries
CREATE INDEX IF NOT EXISTS idx_daily_agg_ticker_date
ON daily_agg(ticker, date DESC);


-- Enable Row Level Security (optional, recommended for production)
-- ALTER TABLE articles ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE mentions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE daily_agg ENABLE ROW LEVEL SECURITY;

-- Create policies (example: allow all for anon key - adjust for your needs)
-- CREATE POLICY "Allow all operations" ON articles FOR ALL USING (true);
-- CREATE POLICY "Allow all operations" ON mentions FOR ALL USING (true);
-- CREATE POLICY "Allow all operations" ON daily_agg FOR ALL USING (true);
