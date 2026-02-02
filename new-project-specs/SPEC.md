# Company Signals Tracker - Project Specification

## Overview

A lightweight tool for tracking newsworthy events at public companies to support sales outreach and prospecting. Built for investor relations and sales teams who need to monitor hundreds of companies for actionable signals.

## Problem Statement

Sales and IR teams need to know when target companies have newsworthy events (leadership changes, funding, expansion, etc.) that create outreach opportunities. Manually monitoring 100-1000 companies is impractical.

## Solution

Automated pipeline that:
1. Monitors news for a watchlist of public companies
2. Uses AI to classify and summarize relevant events
3. Surfaces actionable signals in a simple dashboard
4. Exports data for CRM workflows

## Target Scale

- **Companies tracked**: 100 - 1,000
- **Users**: Single user (MVP)
- **Update frequency**: Daily

---

## Technical Architecture

```
Google News RSS → Fetch Articles → Claude Haiku Classification → Supabase → Streamlit Dashboard
                                                                      ↓
                                                                 CSV Export
```

### Why These Choices

| Component | Choice | Rationale |
|-----------|--------|-----------|
| News source | Google News RSS | Free, no API limits, good public company coverage |
| AI model | Claude 3.5 Haiku | Cheapest, fast, sufficient for classification |
| Database | Supabase (Postgres) | Free tier, familiar from sentiment tracker |
| UI | Streamlit | Free hosting, fast to build, single-page works |

---

## Data Model

### Tables

**companies** (watchlist)
```
id: uuid
name: string (e.g., "Apple Inc.")
ticker: string (e.g., "AAPL")
aliases: string[] (e.g., ["Apple", "AAPL"])
created_at: timestamp
active: boolean
```

**articles**
```
id: uuid
company_id: uuid (FK)
title: string
url: string (unique)
source: string
published_at: timestamp
fetched_at: timestamp
```

**signals**
```
id: uuid
article_id: uuid (FK)
company_id: uuid (FK)
summary: string (1-2 sentences, AI-generated)
signal_type: string (optional, for future categorization)
relevance_score: float (0-1, is this actually about the company?)
created_at: timestamp
```

---

## MVP Features

### 1. Company Watchlist
- Upload CSV or paste list of company names
- Add/remove companies manually
- Store with optional ticker symbol

### 2. News Ingestion
- Daily fetch from Google News RSS for each company
- Deduplicate by URL
- Store headline, source, date, link

### 3. AI Signal Detection
- Send headline + snippet to Claude Haiku
- Get back:
  - 1-2 sentence summary of what happened
  - Relevance score (is this actually about the company?)
- No formal categories yet - start broad, refine later

### 4. Dashboard
- List view of recent signals, newest first
- Filter by company
- Filter by date range
- Search by keyword

### 5. CSV Export
- Export filtered results
- Columns: Company, Date, Headline, Summary, Source, URL
- Manual import to CRM

---

## Deferred Features (Post-MVP)

- **Signal categories**: Leadership, funding, expansion, layoffs, M&A, product news
- **Alerts**: Email digest of new signals
- **CRM integration**: Direct push to HubSpot/Salesforce
- **Team access**: Multi-user with shared watchlist
- **Prioritization**: Rank signals by importance
- **Company enrichment**: Auto-fetch industry, size, location

---

## Cost Estimates

### Monthly Operating Cost

| Service | Usage | Cost |
|---------|-------|------|
| Claude Haiku | ~8,000 articles/month (1000 companies × 2/week avg) | ~$1.60 |
| Supabase | Free tier (500MB) | $0 |
| Streamlit Cloud | Free tier | $0 |
| Google News RSS | Unlimited | $0 |
| **Total** | | **~$2/month** |

### Scaling Notes
- Cost scales linearly with article volume
- At 10,000 articles/month: ~$2/month
- At 100,000 articles/month: ~$20/month

---

## File Structure

```
company-signals-tracker/
├── app.py          # Streamlit UI
├── etl.py          # News fetching + AI classification
├── db.py           # Database operations
├── config.py       # Settings and constants
├── requirements.txt
├── CLAUDE.md       # Instructions for AI collaboration
├── SPEC.md         # This file
└── .streamlit/
    └── secrets.toml  # API keys (not committed)
```

---

## Success Criteria

1. **Add 100 companies in under 5 minutes** (CSV upload)
2. **See today's signals in one glance** (dashboard loads fast)
3. **Export to CSV in one click** (CRM workflow)
4. **Run for under $5/month** (cost efficient)
5. **Deploy in under 10 minutes** (Streamlit Cloud)

---

## Open Questions

1. How to handle company name disambiguation? (e.g., "Apple" the company vs. apple the fruit)
   - Likely: Use ticker symbol + company name in search query

2. How often do we re-fetch news?
   - Likely: Once daily, overnight batch job

3. What's the minimum relevance score to show?
   - Likely: Start at 0.5, tune based on noise level

---

## References

- Similar project: [investor-sentiment-tracker](../investor-sentiment-tracker)
- Google News RSS format: `https://news.google.com/rss/search?q={company}`
- Claude Haiku pricing: ~$0.25/1M input tokens, $1.25/1M output tokens
