"""
Configuration and settings for Investor Sentiment Tracker.
All API keys and constants live here.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file (local dev)
load_dotenv()


# ==================== API CREDENTIALS ====================

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")


# ==================== APP SETTINGS ====================

# Default ticker to track
DEFAULT_TICKER = os.getenv("DEFAULT_TICKER", "TSLA")

# Available tickers for dropdown (hottest stocks)
AVAILABLE_TICKERS = ["TSLA", "NVDA", "AAPL", "GOOGL", "AMZN"]

# Ticker search terms (includes company names for better article coverage)
TICKER_SEARCH_TERMS = {
    "TSLA": "TSLA OR Tesla",
    "NVDA": "NVDA OR Nvidia",
    "AAPL": "AAPL OR Apple",
    "GOOGL": "GOOGL OR Google OR Alphabet",
    "AMZN": "AMZN OR Amazon"
}

# Maximum articles to fetch total (cost control)
# Split across weekly chunks for better time distribution
# ~100 articles = 3-4 per day over 30 days
# With Haiku: ~$0.025 per full run, ~$0.75/month
MAX_ARTICLES_PER_REQUEST = int(os.getenv("MAX_ARTICLES_PER_REQUEST", "100"))

# Date range options (days)
DATE_RANGE_OPTIONS = {
    "Last 7 days": 7,
    "Last 14 days": 14,
    "Last 30 days": 30
}

# Source quality options
SOURCE_QUALITY_OPTIONS = {
    "Quality (Major Sources)": "quality",
    "Quantity (All Sources)": "quantity"
}

# Major US financial news sources for "quality" mode
MAJOR_NEWS_DOMAINS = [
    "wsj.com",
    "bloomberg.com",
    "reuters.com",
    "cnbc.com",
    "ft.com",
    "marketwatch.com",
    "businessinsider.com",
    "forbes.com",
    "fortune.com",
    "barrons.com"
]


# ==================== API SETTINGS ====================

# NewsAPI
NEWS_API_BASE_URL = "https://newsapi.org/v2"
NEWS_SEARCH_LANGUAGE = "en"
NEWS_SORT_BY = "publishedAt"  # or 'relevancy', 'popularity'

# Claude API
CLAUDE_MODEL = "claude-3-5-haiku-20241022"  # Using Haiku for cost efficiency
CLAUDE_MAX_TOKENS = 500
CLAUDE_TEMPERATURE = 0.0  # Deterministic for consistent sentiment scores


# ==================== PROMPTS ====================

SENTIMENT_PROMPT = """Analyze investor sentiment toward {ticker} in this article.

Title: {title}
Snippet: {snippet}

Return valid JSON only:
{{
  "sentiment": <float -1.0 to 1.0>,
  "label": "<negative|neutral|positive>",
  "topics": ["<topic1>", "<topic2>"]
}}

Rules:
- sentiment: -1.0 (very negative) to 1.0 (very positive)
- label: must be exactly "negative", "neutral", or "positive"
- topics: max 3 topics, each 2-4 words, ALWAYS USE LOWERCASE, be consistent with naming
  Examples: "regulatory concerns", "earnings performance", "product launch", "market volatility"
"""

BRIEF_PROMPT = """Create a 3-sentence IR brief for {ticker} based on today's coverage.

Articles analyzed: {article_count}
Average sentiment: {avg_sentiment:.2f} ({sentiment_label})
Top topics: {top_topics}

Sample headlines:
{headlines}

Format:
1. Overall tone assessment (1 sentence)
2. Key narrative or theme (1 sentence)
3. Notable mention or shift (1 sentence)

Keep it factual and concise. No fluff."""

CHAT_PROMPT = """You are an IR analyst assistant. Your task is to answer questions regarding the investor sentiment of the stock represented by {ticker}. Use exclusively the following data to formulate your responses:

SENTIMENT SUMMARY:
- Date range: {date_range}
- Average sentiment: {avg_sentiment:.2f}
- Total articles analyzed: {article_count}
- Trend: {trend}

DAILY BRIEFS:
{daily_briefs}

KEY ARTICLES:
{key_articles}

User question: {question}

Your answer should be concise and factual, limited to 2-3 sentences. If the information provided does not allow for a valid answer, please indicate that explicitly."""


# ==================== SENTIMENT THRESHOLDS ====================

SENTIMENT_THRESHOLDS = {
    "positive": 0.25,   # >= 0.25 is positive
    "negative": -0.25,  # <= -0.25 is negative
    # Between -0.25 and 0.25 is neutral
}

TREND_THRESHOLDS = {
    "improving": 0.1,   # 3-day avg increased by >= 0.1
    "declining": -0.1,  # 3-day avg decreased by <= -0.1
    # Otherwise "stable"
}


# ==================== VALIDATION ====================

def validate_config():
    """Check if all required credentials are set."""
    missing = []

    if not NEWS_API_KEY:
        missing.append("NEWS_API_KEY")
    if not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not SUPABASE_KEY:
        missing.append("SUPABASE_KEY")

    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"Please set them in .env file or Streamlit secrets."
        )

    return True


if __name__ == "__main__":
    # Test config
    try:
        validate_config()
        print("✓ All config variables set")
        print(f"✓ Default ticker: {DEFAULT_TICKER}")
        print(f"✓ Max articles/day: {MAX_ARTICLES_PER_DAY}")
    except ValueError as e:
        print(f"✗ Config error: {e}")
