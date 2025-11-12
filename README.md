# Investor Sentiment Tracker

> Monitor media sentiment for major tech stocks with AI-powered analysis and interactive visualizations

A portfolio project by **Nicolo Pastrone** demonstrating modern AI-assisted development and full-stack web application skills.

## Overview

Track how media sentiment toward major tech stocks (TSLA, NVDA, AAPL, GOOGL, AMZN) shifts over time. Get AI-generated insights, visualize trends, and ask questions about the data—all powered by Claude 3.5 Haiku for cost-efficient sentiment analysis.

### Key Features

- **Real-time Sentiment Analysis**: AI-powered analysis of financial news with Claude 3.5 Haiku
- **Interactive Dashboard**: 2x2 grid with Daily IR Briefs, Sentiment Trends (7-day MA), Article Volume, and Top Topics
- **AI Q&A Chatbot**: Ask questions about sentiment trends and get instant insights
- **Source Quality Control**: Toggle between major financial outlets or all sources
- **Cost-Efficient**: ~$0.75/month for daily updates using Claude Haiku
- **Persistent Storage**: Supabase PostgreSQL database with automatic deduplication

## Technical Implementation

**Built by Nicolo Pastrone** with:
- **Frontend**: Python + Streamlit for responsive web interface
- **AI/ML**: Anthropic's Claude 3.5 Haiku API with custom prompt engineering
- **Database**: Supabase (PostgreSQL) with row-level security
- **Data Source**: NewsAPI with configurable source filtering
- **Development**: Collaboratively built with Claude Code, demonstrating modern AI-assisted workflows

### Architecture

```
NewsAPI → ETL Pipeline → Claude 3.5 Haiku → Supabase PostgreSQL → Streamlit UI
                          (Sentiment Analysis)
```

## Quick Start

### Prerequisites

- Python 3.9+
- Free API keys:
  - [NewsAPI](https://newsapi.org/) (100 requests/day free)
  - [Anthropic Claude](https://console.anthropic.com/) ($5 free credit)
  - [Supabase](https://supabase.com/) (free tier with 500MB database)

### Local Setup

1. **Clone and install dependencies**:
```bash
git clone https://github.com/yourusername/investor-sentiment-tracker.git
cd investor-sentiment-tracker
pip install -r requirements.txt
```

2. **Set up Supabase database**:
   - Create a new project at [supabase.com](https://supabase.com)
   - Go to SQL Editor and run the contents of `schema.sql`
   - Copy your project URL and anon key

3. **Create `.env` file** (use `.env.example` as template):
```bash
NEWS_API_KEY=your_newsapi_key_here
ANTHROPIC_API_KEY=your_claude_key_here
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here
DEFAULT_TICKER=TSLA
MAX_ARTICLES_PER_REQUEST=100
```

4. **Run locally**:
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## Deploy to Streamlit Cloud (Free)

1. **Push to GitHub**:
```bash
git remote add origin https://github.com/yourusername/investor-sentiment-tracker.git
git push -u origin main
```

2. **Deploy**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app" and connect your GitHub repo
   - Add secrets in "Advanced settings" → "Secrets":
     ```toml
     NEWS_API_KEY = "your_key"
     ANTHROPIC_API_KEY = "your_key"
     SUPABASE_URL = "your_url"
     SUPABASE_KEY = "your_key"
     ```
   - Click "Deploy"

3. **Done!** Your app will be live at `https://your-app.streamlit.app`

## Project Structure

```
investor-sentiment-tracker/
├── app.py              # Streamlit UI with 2x2 dashboard grid
├── etl.py              # Data extraction, Claude AI analysis, daily summaries
├── db.py               # Supabase database operations
├── config.py           # API settings, prompts, and configuration
├── schema.sql          # PostgreSQL database schema
├── requirements.txt    # Python dependencies
├── PLANNING.md         # Comprehensive technical plan
├── CLAUDE.md          # AI-assisted development guide
└── .env.example       # Environment variables template
```

## Cost Breakdown

| Service | Plan | Cost |
|---------|------|------|
| **Streamlit Cloud** | Free tier | $0/month |
| **NewsAPI** | Free tier (100 req/day) | $0/month |
| **Supabase** | Free tier (500MB) | $0/month |
| **Claude 3.5 Haiku** | Pay-as-you-go | ~$0.75/month* |

*Based on daily tracking of 5 companies with ~3 articles/day each (~450 articles/month at ~$0.0017 per article)

## What I Learned

This project demonstrates:
- **AI Integration**: Custom prompt engineering for consistent sentiment scoring
- **Full-Stack Development**: Python backend, Supabase database, Streamlit frontend
- **Cost Optimization**: Strategic use of Haiku model instead of Sonnet for 10x cost reduction
- **Data Pipeline Design**: ETL architecture with deduplication and chunked processing
- **UX Design**: Intuitive dashboard layout with real-time feedback
- **AI-Assisted Development**: Built collaboratively with Claude Code

## Future Enhancements

- [ ] Multi-company comparison view
- [ ] Email alerts for sentiment shifts
- [ ] Export data to CSV/PDF
- [ ] Historical sentiment correlation with stock price
- [ ] Social media sentiment (Twitter/Reddit)
- [ ] Custom company ticker support

## License

MIT License - Feel free to use this project for learning or portfolio purposes.

## About

**Nicolo Pastrone** | [Portfolio](https://your-portfolio.com) | [LinkedIn](https://linkedin.com/in/yourprofile) | [GitHub](https://github.com/yourusername)

Built as a portfolio project to demonstrate AI integration, full-stack development, and modern development workflows.
