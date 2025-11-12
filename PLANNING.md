# Investor Sentiment Tracker - MVP Planning

## Project Summary

**Problem**: IR teams lack visibility into how investor sentiment toward their company shifts over time across media and analyst coverage.

**Target User**: Investor Relations professionals at public companies who need to track narrative trends without expensive monitoring tools.

**Headline Insight**: Surface sentiment trajectory + key narrative drivers in a simple daily brief format.

---

## System Overview

```
User → Streamlit UI
         ↓
    Python ETL (daily cron)
         ↓
    SQLite database
         ↓
    External APIs (news, financials)
         ↓
    Claude API (sentiment + summarization)
```

**Architecture Philosophy**: Single-server app. ETL runs on-demand or scheduled. All state in SQLite. Claude calls cached and batched.

---

## Data Sources

1. **NewsAPI** (free tier: 100 req/day, 30-day history)
   - Company mentions in business news
   - Alternative: Alpha Vantage News

2. **FinancialModelingPrep** (free tier: 250 req/day)
   - Stock price, basic fundamentals
   - Alternative: yfinance (no key needed)

3. **Optional**: Reddit Finance API (free, rate-limited)
   - Retail sentiment from r/wallstreetbets, r/stocks

**Cost Control**: Cache API responses for 24h. Sample max 20 articles/day for LLM analysis.

---

## Data Model

### Schema (SQLite)

```sql
-- Raw article storage
CREATE TABLE articles (
    id INTEGER PRIMARY KEY,
    source TEXT,
    title TEXT,
    url TEXT,
    published_at TEXT,
    content_snippet TEXT,
    fetched_at TEXT,
    UNIQUE(url)
);

-- Company mentions with sentiment
CREATE TABLE mentions (
    id INTEGER PRIMARY KEY,
    article_id INTEGER,
    company_ticker TEXT,
    sentiment_score REAL,  -- -1.0 to 1.0
    sentiment_label TEXT,  -- negative/neutral/positive
    key_topics TEXT,       -- JSON array
    analyzed_at TEXT,
    FOREIGN KEY(article_id) REFERENCES articles(id)
);

-- Daily aggregates
CREATE TABLE daily_agg (
    date TEXT PRIMARY KEY,
    ticker TEXT,
    avg_sentiment REAL,
    article_count INTEGER,
    sentiment_trend TEXT,  -- improving/stable/declining
    top_topics TEXT,       -- JSON array
    ir_brief TEXT,         -- Claude-generated summary
    created_at TEXT
);
```

---

## ETL Pipeline

### Steps (etl.py)

1. **Extract** (extract_news)
   - Fetch articles from NewsAPI for target ticker
   - Deduplicate against existing URLs
   - Store in `articles` table

2. **Transform** (analyze_sentiment)
   - For each new article, call Claude with:
     - Prompt: "Analyze sentiment toward [TICKER]. Return JSON: {sentiment: -1 to 1, label: string, topics: [string]}."
     - Max tokens: 200
   - Store results in `mentions` table
   - Cache Claude responses by article_id

3. **Aggregate** (create_daily_summary)
   - Group mentions by date
   - Calculate avg_sentiment, count, trend (3-day moving avg)
   - Extract top 3 topics

4. **Summarize** (generate_ir_brief)
   - Batch prompt to Claude: "Summarize today's investor sentiment. Include: overall tone, key narrative shifts, notable articles. Max 3 sentences."
   - Store in `daily_agg.ir_brief`

**Caching Strategy**:
- Article content cached 30 days
- Claude sentiment analysis cached permanently
- Daily summary regenerated only if new articles exist

---

## LLM Use

### Primary Prompt (sentiment analysis)

```python
SENTIMENT_PROMPT = """
Analyze investor sentiment toward {ticker} in this article.

Title: {title}
Snippet: {snippet}

Return valid JSON only:
{{
  "sentiment": <float -1.0 to 1.0>,
  "label": "<negative|neutral|positive>",
  "topics": ["<topic1>", "<topic2>"]
}}
"""
```

### Secondary Prompt (daily brief)

```python
BRIEF_PROMPT = """
Create a 3-sentence IR brief for {ticker} based on today's coverage:

Articles: {article_summaries}
Avg Sentiment: {avg_sentiment}

Format:
1. Overall tone assessment
2. Key narrative shift (if any)
3. Notable mention
"""
```

### Cost Controls
- Max 20 articles analyzed per day = ~4,000 input tokens + ~4,000 output = $0.10/day
- Cache article analysis results forever
- Use Claude 3.5 Sonnet (balances cost/quality)
- Monthly estimate: ~$3

---

## UI Plan (Streamlit)

### Single-Page Layout (app.py)

**Header**
- Company ticker selector (default: TSLA, AAPL, MSFT)
- Date range picker (last 7/30/90 days)

**Main Dashboard**
1. **Sentiment Trend Chart** (line chart)
   - X: dates, Y: avg_sentiment (-1 to 1)
   - Color zones: red (negative), yellow (neutral), green (positive)

2. **Volume Chart** (bar chart)
   - X: dates, Y: article count

3. **IR Brief Card** (highlighted box)
   - Display `daily_agg.ir_brief` for selected date
   - Include sentiment label badge

4. **Topic Cloud** (expandable section)
   - Top 10 topics from date range, sized by frequency

5. **Recent Articles Table** (bottom)
   - Columns: Date, Source, Title (linked), Sentiment
   - Sortable, max 20 rows

**Interactivity**
- Click chart point → update IR Brief card to that date
- Refresh button → trigger ETL for today

---

## Repo Layout

```
/
├── app.py              # Streamlit UI (main entry)
├── etl.py              # Extract, transform, aggregate logic
├── db.py               # SQLite setup, queries, schema
├── config.py           # API keys, constants, settings
├── requirements.txt    # Dependencies
├── README.md           # User-facing: what it does, how to run
├── CLAUDE.md           # Dev-facing: how to collaborate with Claude
└── PLANNING.md         # This file
```

**Target**: 6-7 files max. No separate folders until file count >10.

---

## Build Sequence

### Milestone 1: Database + Config (1h)
- [ ] Create `db.py` with schema setup
- [ ] Create `config.py` with API key placeholders
- [ ] Add `.env` support for secrets
- [ ] Test SQLite initialization

### Milestone 2: ETL Extraction (1h)
- [ ] Implement `extract_news()` in `etl.py`
- [ ] Connect to NewsAPI
- [ ] Store articles in database
- [ ] Handle deduplication

### Milestone 3: Sentiment Analysis (1.5h)
- [ ] Implement `analyze_sentiment()` with Claude API
- [ ] Parse JSON responses
- [ ] Store in `mentions` table
- [ ] Add basic error handling

### Milestone 4: Aggregation (1h)
- [ ] Implement `create_daily_summary()`
- [ ] Calculate sentiment trends
- [ ] Extract top topics
- [ ] Generate IR brief with Claude

### Milestone 5: Streamlit UI (2h)
- [ ] Build basic layout in `app.py`
- [ ] Add sentiment trend chart (Plotly/Altair)
- [ ] Display IR brief card
- [ ] Add article table

### Milestone 6: Polish + Deploy (1h)
- [ ] Add refresh button
- [ ] Configure Streamlit secrets
- [ ] Test on Streamlit Cloud
- [ ] Add basic error messages

**Total Estimated Time**: 7.5 hours (realistic weekend build)

---

## Cost + Hosting Notes

### Free Tier Limits
- **NewsAPI**: 100 requests/day (sufficient for 5 companies)
- **Streamlit Cloud**: Free hosting, auto-deploys from GitHub
- **Claude API**: Pay-as-you-go (~$3/month for 20 articles/day)
- **SQLite**: Local file, no hosting cost

### Deployment Checklist
1. Store API keys in Streamlit secrets (not .env in production)
2. Set `secrets.toml` with:
   ```toml
   NEWS_API_KEY = "..."
   ANTHROPIC_API_KEY = "..."
   ```
3. Add `requirements.txt`:
   ```
   streamlit
   anthropic
   requests
   plotly
   pandas
   ```
4. Deploy from GitHub repo (must be public for free tier)

### Cost Optimization
- Cache all Claude responses in database
- Limit analysis to 20 most relevant articles per day
- Use short, structured prompts (JSON output)
- Consider batch processing articles (5 at once) if API supports

### Optional: Supabase Migration
If SQLite becomes limiting:
- Create Supabase free tier project
- Replace `db.py` connection string
- Keep same schema
- Benefit: persistent storage across Streamlit restarts

---

## Success Metrics

**MVP Success = Can answer these questions:**
1. Is sentiment toward [TICKER] improving or declining this week?
2. What topics are driving the narrative?
3. Which articles are most negative/positive?

**Not in MVP:**
- Multi-user support
- Email alerts
- Historical backtesting >90 days
- Social media integration beyond basic Reddit

**Next Phase Ideas** (post-MVP):
- Competitor comparison view
- Sentiment correlation with stock price
- Weekly email digest
- Custom topic tracking
