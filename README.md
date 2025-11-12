# Investor Sentiment Tracker

A simple Streamlit app that helps IR teams track how media sentiment toward their company is shifting over time.

## What It Does

- Fetches daily news articles mentioning your company ticker
- Uses Claude AI to analyze sentiment and extract key topics
- Shows sentiment trends, article volume, and an AI-generated IR brief
- Runs entirely on free-tier services

## Quick Start

### Prerequisites
- Python 3.9+
- API keys (free tier):
  - [NewsAPI](https://newsapi.org/)
  - [Anthropic Claude](https://console.anthropic.com/)

### Local Setup

1. Clone and install:
```bash
git clone <repo-url>
cd investor-sentiment-tracker
pip install -r requirements.txt
```

2. Create `.env` file:
```bash
NEWS_API_KEY=your_newsapi_key
ANTHROPIC_API_KEY=your_claude_key
DEFAULT_TICKER=TSLA
```

3. Run:
```bash
streamlit run app.py
```

## Deploy to Streamlit Cloud (Free)

1. Push code to GitHub (public repo)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repo and add secrets in dashboard:
   - `NEWS_API_KEY`
   - `ANTHROPIC_API_KEY`
4. Deploy

## File Structure

- `app.py` - Streamlit UI
- `etl.py` - Data extraction and sentiment analysis
- `db.py` - SQLite database setup and queries
- `config.py` - Settings and API configuration
- `PLANNING.md` - Full technical plan
- `CLAUDE.md` - Guide for AI-assisted development

## Cost

- NewsAPI: Free (100 req/day)
- Claude API: ~$3/month (20 articles/day)
- Hosting: Free (Streamlit Cloud)

## Limitations

- 30-day article history (NewsAPI free tier)
- Single company tracking per instance
- No real-time updates (manual refresh)

## Support

For issues or questions, see [CLAUDE.md](CLAUDE.md) for development guidance.
