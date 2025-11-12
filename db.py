"""
Database layer for Investor Sentiment Tracker.
Uses Supabase (PostgreSQL) for persistent storage.
"""

import os
from datetime import datetime
from typing import List, Dict, Optional
from supabase import create_client, Client


class Database:
    """Handles all database operations."""

    def __init__(self):
        """Initialize Supabase connection."""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY environment variables")

        self.client: Client = create_client(supabase_url, supabase_key)

    def initialize_schema(self):
        """
        Create tables if they don't exist.
        Run this once on first deployment.

        Note: For Supabase, you can also create tables via SQL editor in dashboard:
        https://app.supabase.com/project/_/editor
        """
        # Supabase tables are typically created via the web UI or migrations
        # This method is a placeholder for schema documentation
        pass

    # ==================== ARTICLES ====================

    def insert_article(self, source: str, title: str, url: str,
                      published_at: str, content_snippet: str) -> Optional[int]:
        """
        Insert a new article. Returns article_id if inserted, None if duplicate.
        """
        try:
            result = self.client.table("articles").insert({
                "source": source,
                "title": title,
                "url": url,
                "published_at": published_at,
                "content_snippet": content_snippet,
                "fetched_at": datetime.now().isoformat()
            }).execute()

            return result.data[0]["id"] if result.data else None
        except Exception as e:
            # Likely duplicate URL (unique constraint)
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                return None
            raise

    def get_article_by_url(self, url: str) -> Optional[Dict]:
        """Check if article already exists."""
        result = self.client.table("articles")\
            .select("*")\
            .eq("url", url)\
            .execute()

        return result.data[0] if result.data else None

    def get_articles_by_date_range(self, ticker: str, start_date: str,
                                   end_date: str) -> List[Dict]:
        """Get articles for a ticker within date range."""
        result = self.client.table("articles")\
            .select("*, mentions!inner(*)")\
            .eq("mentions.company_ticker", ticker)\
            .gte("published_at", start_date)\
            .lte("published_at", end_date)\
            .order("published_at", desc=True)\
            .execute()

        return result.data

    # ==================== MENTIONS ====================

    def insert_mention(self, article_id: int, company_ticker: str,
                      sentiment_score: float, sentiment_label: str,
                      key_topics: List[str]) -> int:
        """Insert sentiment analysis for an article."""
        result = self.client.table("mentions").insert({
            "article_id": article_id,
            "company_ticker": company_ticker,
            "sentiment_score": sentiment_score,
            "sentiment_label": sentiment_label,
            "key_topics": key_topics,  # Supabase handles JSON automatically
            "analyzed_at": datetime.now().isoformat()
        }).execute()

        return result.data[0]["id"]

    def get_mention_by_article(self, article_id: int) -> Optional[Dict]:
        """Check if article has already been analyzed."""
        result = self.client.table("mentions")\
            .select("*")\
            .eq("article_id", article_id)\
            .execute()

        return result.data[0] if result.data else None

    def get_mentions_by_date(self, ticker: str, date: str) -> List[Dict]:
        """Get all mentions for a ticker on a specific date."""
        # First get articles for the date
        articles_result = self.client.table("articles")\
            .select("id")\
            .gte("published_at", f"{date}T00:00:00")\
            .lt("published_at", f"{date}T23:59:59")\
            .execute()

        if not articles_result.data:
            return []

        article_ids = [a["id"] for a in articles_result.data]

        # Then get mentions for those articles
        result = self.client.table("mentions")\
            .select("*, articles(*)")\
            .eq("company_ticker", ticker)\
            .in_("article_id", article_ids)\
            .execute()

        return result.data

    # ==================== DAILY AGGREGATES ====================

    def insert_daily_agg(self, date: str, ticker: str, avg_sentiment: float,
                        article_count: int, sentiment_trend: str,
                        top_topics: List[str], ir_brief: str) -> str:
        """Insert or update daily aggregate."""
        result = self.client.table("daily_agg").upsert({
            "date": date,
            "ticker": ticker,
            "avg_sentiment": avg_sentiment,
            "article_count": article_count,
            "sentiment_trend": sentiment_trend,
            "top_topics": top_topics,
            "ir_brief": ir_brief,
            "created_at": datetime.now().isoformat()
        }).execute()

        return result.data[0]["date"]

    def get_daily_agg(self, ticker: str, date: str) -> Optional[Dict]:
        """Get daily aggregate for a specific date."""
        result = self.client.table("daily_agg")\
            .select("*")\
            .eq("ticker", ticker)\
            .eq("date", date)\
            .execute()

        return result.data[0] if result.data else None

    def get_daily_agg_range(self, ticker: str, start_date: str,
                           end_date: str) -> List[Dict]:
        """Get daily aggregates for date range."""
        result = self.client.table("daily_agg")\
            .select("*")\
            .eq("ticker", ticker)\
            .gte("date", start_date)\
            .lte("date", end_date)\
            .order("date", desc=False)\
            .execute()

        return result.data


# Singleton instance
_db_instance: Optional[Database] = None


def get_db() -> Database:
    """Get or create database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
