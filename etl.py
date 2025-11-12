"""
ETL pipeline for Investor Sentiment Tracker.
Extracts news, analyzes sentiment with Claude, aggregates daily summaries.
"""

import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from anthropic import Anthropic

import config
from db import get_db


# ==================== EXTRACTION ====================

def extract_news(ticker: str, days_back: int = 7, source_filter: Optional[str] = None) -> List[Dict]:
    """
    Fetch news articles for a ticker from NewsAPI with time distribution.
    Fetches articles in weekly chunks to ensure coverage across full date range.

    Args:
        ticker: Stock ticker symbol
        days_back: Number of days to look back
        source_filter: "quality" for major sources only, "quantity" or None for all sources

    Returns list of articles with deduplication.
    """
    db = get_db()
    url = f"{config.NEWS_API_BASE_URL}/everything"
    all_new_articles = []

    # Calculate date range
    to_date = datetime.now()
    from_date = to_date - timedelta(days=days_back)

    # Split into weekly chunks for better time distribution
    # For 30 days, this gives us ~4 chunks, each fetching ~10-15 articles
    chunk_size = 7  # days per chunk
    articles_per_chunk = max(10, config.MAX_ARTICLES_PER_REQUEST // (days_back // chunk_size + 1))

    current_end = to_date
    while current_end > from_date:
        current_start = max(from_date, current_end - timedelta(days=chunk_size))

        # Build NewsAPI request with company name search
        # Use company name aliases (e.g., "GOOGL OR Google OR Alphabet") for better coverage
        search_term = config.TICKER_SEARCH_TERMS.get(ticker, ticker)

        params = {
            "q": search_term,
            "apiKey": config.NEWS_API_KEY,
            "language": config.NEWS_SEARCH_LANGUAGE,
            "sortBy": "relevancy",  # Better time distribution than publishedAt
            "from": current_start.strftime("%Y-%m-%d"),
            "to": current_end.strftime("%Y-%m-%d"),
            "pageSize": articles_per_chunk
        }

        # Add domain filtering for "quality" mode
        if source_filter == "quality":
            params["domains"] = ",".join(config.MAJOR_NEWS_DOMAINS)

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data["status"] != "ok":
                print(f"NewsAPI warning for {current_start.strftime('%Y-%m-%d')} to {current_end.strftime('%Y-%m-%d')}: {data.get('message', 'Unknown error')}")
                current_end = current_start
                continue

            articles = data.get("articles", [])
            print(f"Fetched {len(articles)} articles for {current_start.strftime('%Y-%m-%d')} to {current_end.strftime('%Y-%m-%d')}")

            # Insert articles, skip duplicates
            for article in articles:
                # Skip if missing required fields
                if not article.get("url") or not article.get("title"):
                    continue

                # Check if already exists
                existing = db.get_article_by_url(article["url"])
                if existing:
                    continue

                # Insert new article
                article_id = db.insert_article(
                    source=article.get("source", {}).get("name", "Unknown"),
                    title=article["title"],
                    url=article["url"],
                    published_at=article.get("publishedAt", datetime.now().isoformat()),
                    content_snippet=article.get("description", "") or article.get("content", "")[:500]
                )

                if article_id:
                    all_new_articles.append({
                        "id": article_id,
                        "title": article["title"],
                        "url": article["url"],
                        "published_at": article.get("publishedAt"),
                        "content_snippet": article.get("description", "") or article.get("content", "")[:500]
                    })

        except Exception as e:
            print(f"Error fetching chunk {current_start.strftime('%Y-%m-%d')} to {current_end.strftime('%Y-%m-%d')}: {str(e)}")

        # Move to next chunk
        current_end = current_start

    print(f"Total new articles fetched: {len(all_new_articles)}")
    return all_new_articles


# ==================== SENTIMENT ANALYSIS ====================

def analyze_sentiment(article_id: int, ticker: str, title: str,
                     snippet: str) -> Optional[Dict]:
    """
    Analyze sentiment for an article using Claude API.
    Returns sentiment data or None if already analyzed.
    """
    db = get_db()

    # Check if already analyzed (caching)
    existing = db.get_mention_by_article(article_id)
    if existing:
        return existing

    # Build prompt
    prompt = config.SENTIMENT_PROMPT.format(
        ticker=ticker,
        title=title,
        snippet=snippet[:500]  # Limit snippet length
    )

    # Call Claude API
    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

    try:
        message = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=config.CLAUDE_MAX_TOKENS,
            temperature=config.CLAUDE_TEMPERATURE,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # Parse JSON response
        response_text = message.content[0].text.strip()

        # Handle markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        # Extract just the JSON object (in case Claude adds explanation after)
        # Find first { and last }
        first_brace = response_text.find("{")
        last_brace = response_text.rfind("}")

        if first_brace != -1 and last_brace != -1:
            response_text = response_text[first_brace:last_brace + 1]

        sentiment_data = json.loads(response_text)

        # Validate response
        if not all(k in sentiment_data for k in ["sentiment", "label", "topics"]):
            raise ValueError("Missing required fields in Claude response")

        # Normalize topics (lowercase, strip whitespace, deduplicate)
        normalized_topics = []
        seen_topics = set()
        for topic in sentiment_data.get("topics", []):
            normalized = topic.lower().strip()
            # Only add if not already seen (case-insensitive deduplication)
            if normalized and normalized not in seen_topics:
                normalized_topics.append(normalized)
                seen_topics.add(normalized)
        sentiment_data["topics"] = normalized_topics

        # Normalize sentiment label
        label = sentiment_data["label"].lower()
        if label not in ["negative", "neutral", "positive"]:
            # Fallback based on score
            score = sentiment_data["sentiment"]
            if score >= config.SENTIMENT_THRESHOLDS["positive"]:
                label = "positive"
            elif score <= config.SENTIMENT_THRESHOLDS["negative"]:
                label = "negative"
            else:
                label = "neutral"

        # Insert into database
        mention_id = db.insert_mention(
            article_id=article_id,
            company_ticker=ticker,
            sentiment_score=float(sentiment_data["sentiment"]),
            sentiment_label=label,
            key_topics=sentiment_data["topics"]
        )

        return {
            "id": mention_id,
            "sentiment_score": sentiment_data["sentiment"],
            "sentiment_label": label,
            "key_topics": sentiment_data["topics"]
        }

    except Exception as e:
        print(f"Error analyzing article {article_id}: {str(e)}")
        return None


# ==================== AGGREGATION ====================

def create_daily_summary(ticker: str, date: str) -> Optional[Dict]:
    """
    Create daily aggregate for a ticker and date.
    Returns summary data.
    """
    db = get_db()

    # Get all mentions for the day
    mentions = db.get_mentions_by_date(ticker, date)

    if not mentions:
        return None

    # Calculate average sentiment
    sentiments = [m["sentiment_score"] for m in mentions]
    avg_sentiment = sum(sentiments) / len(sentiments)

    # Determine trend (compare with previous days if available)
    sentiment_trend = "stable"
    try:
        prev_date = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=3)).strftime("%Y-%m-%d")
        prev_agg = db.get_daily_agg(ticker, prev_date)
        if prev_agg:
            diff = avg_sentiment - prev_agg["avg_sentiment"]
            if diff >= config.TREND_THRESHOLDS["improving"]:
                sentiment_trend = "improving"
            elif diff <= config.TREND_THRESHOLDS["declining"]:
                sentiment_trend = "declining"
    except:
        pass

    # Extract top topics
    all_topics = []
    for m in mentions:
        if m.get("key_topics"):
            all_topics.extend(m["key_topics"])

    # Count topic frequency
    topic_counts = {}
    for topic in all_topics:
        topic_counts[topic] = topic_counts.get(topic, 0) + 1

    # Get top 5 topics
    top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    top_topics = [t[0] for t in top_topics]

    # Generate IR brief
    ir_brief = generate_ir_brief(ticker, mentions, avg_sentiment, top_topics)

    # Insert into database
    db.insert_daily_agg(
        date=date,
        ticker=ticker,
        avg_sentiment=avg_sentiment,
        article_count=len(mentions),
        sentiment_trend=sentiment_trend,
        top_topics=top_topics,
        ir_brief=ir_brief
    )

    return {
        "date": date,
        "ticker": ticker,
        "avg_sentiment": avg_sentiment,
        "article_count": len(mentions),
        "sentiment_trend": sentiment_trend,
        "top_topics": top_topics,
        "ir_brief": ir_brief
    }


def generate_ir_brief(ticker: str, mentions: List[Dict],
                     avg_sentiment: float, top_topics: List[str]) -> str:
    """
    Generate IR brief using Claude API.
    """
    # Determine sentiment label
    if avg_sentiment >= config.SENTIMENT_THRESHOLDS["positive"]:
        sentiment_label = "positive"
    elif avg_sentiment <= config.SENTIMENT_THRESHOLDS["negative"]:
        sentiment_label = "negative"
    else:
        sentiment_label = "neutral"

    # Get sample headlines (top 5 by sentiment extremity)
    sorted_mentions = sorted(mentions, key=lambda x: abs(x["sentiment_score"]), reverse=True)
    headlines = []
    for m in sorted_mentions[:5]:
        if "articles" in m and m["articles"]:
            headlines.append(f"- {m['articles']['title']}")

    headlines_text = "\n".join(headlines) if headlines else "No significant headlines"

    # Build prompt
    prompt = config.BRIEF_PROMPT.format(
        ticker=ticker,
        article_count=len(mentions),
        avg_sentiment=avg_sentiment,
        sentiment_label=sentiment_label,
        top_topics=", ".join(top_topics) if top_topics else "No clear topics",
        headlines=headlines_text
    )

    # Call Claude API
    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

    try:
        message = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=config.CLAUDE_MAX_TOKENS,
            temperature=0.3,  # Slightly creative for brief
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        brief = message.content[0].text.strip()
        return brief

    except Exception as e:
        print(f"Error generating IR brief: {str(e)}")
        return f"Analyzed {len(mentions)} articles with {sentiment_label} sentiment ({avg_sentiment:.2f}). Top topics: {', '.join(top_topics[:3])}."


# ==================== PIPELINE ORCHESTRATION ====================

def run_pipeline(ticker: str, days_back: int = 7) -> Dict:
    """
    Run full ETL pipeline for a ticker.
    Returns summary of results.
    """
    results = {
        "ticker": ticker,
        "articles_fetched": 0,
        "articles_analyzed": 0,
        "days_summarized": 0,
        "errors": []
    }

    try:
        # Step 1: Extract news
        print(f"Extracting news for {ticker}...")
        new_articles = extract_news(ticker, days_back)
        results["articles_fetched"] = len(new_articles)

        # Step 2: Analyze sentiment
        print(f"Analyzing {len(new_articles)} articles...")
        for article in new_articles:
            sentiment = analyze_sentiment(
                article_id=article["id"],
                ticker=ticker,
                title=article["title"],
                snippet=article["content_snippet"]
            )
            if sentiment:
                results["articles_analyzed"] += 1

        # Step 3: Create daily summaries
        print(f"Creating daily summaries...")
        dates_to_summarize = set()
        for article in new_articles:
            pub_date = article["published_at"][:10]  # YYYY-MM-DD
            dates_to_summarize.add(pub_date)

        for date in dates_to_summarize:
            summary = create_daily_summary(ticker, date)
            if summary:
                results["days_summarized"] += 1

        print(f"Pipeline complete: {results['articles_analyzed']} articles analyzed, {results['days_summarized']} days summarized")

    except Exception as e:
        error_msg = f"Pipeline error: {str(e)}"
        results["errors"].append(error_msg)
        print(error_msg)

    return results


# ==================== CHAT / Q&A ====================

def answer_sentiment_question(ticker: str, question: str,
                              start_date: str, end_date: str) -> Dict:
    """
    Answer user questions about sentiment using Claude.
    Gathers relevant context and returns answer with related articles.

    Returns:
        {
            "answer": "2-3 sentence response",
            "related_articles": [
                {"title": "...", "url": "...", "source": "...", "date": "...", "sentiment": ...}
            ]
        }
    """
    db = get_db()

    # Get daily aggregates
    daily_data = db.get_daily_agg_range(ticker, start_date, end_date)
    if not daily_data:
        return {
            "answer": "No sentiment data available for this date range. Please fetch articles first.",
            "related_articles": []
        }

    # Calculate summary stats
    sentiments = [d["avg_sentiment"] for d in daily_data]
    avg_sentiment = sum(sentiments) / len(sentiments)
    article_count = sum([d["article_count"] for d in daily_data])

    # Determine overall trend
    if len(sentiments) > 1:
        recent_avg = sum(sentiments[-3:]) / len(sentiments[-3:])
        older_avg = sum(sentiments[:3]) / min(3, len(sentiments[:3]))
        if recent_avg > older_avg + 0.1:
            trend = "improving"
        elif recent_avg < older_avg - 0.1:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = daily_data[0].get("sentiment_trend", "stable")

    # Format daily briefs (last 5 days or all if fewer)
    daily_briefs_text = []
    for d in daily_data[-5:]:
        date = d["date"]
        sentiment = d["avg_sentiment"]
        brief = d["ir_brief"]
        daily_briefs_text.append(f"- {date} (sentiment: {sentiment:.2f}): {brief}")

    # Get key articles (most positive and most negative)
    articles = db.get_articles_by_date_range(ticker, start_date, end_date)
    articles_with_sentiment = []

    for article in articles:
        if article.get("mentions"):
            mention = article["mentions"][0]
            articles_with_sentiment.append({
                "title": article["title"],
                "url": article["url"],
                "date": article["published_at"][:10],
                "sentiment": mention["sentiment_score"],
                "source": article["source"]
            })

    # Sort by sentiment (get top 3 positive and top 3 negative)
    articles_with_sentiment.sort(key=lambda x: x["sentiment"], reverse=True)
    top_positive = articles_with_sentiment[:3]
    top_negative = articles_with_sentiment[-3:]

    # Combine for related articles (top 3 negative + top 2 positive = 5 total)
    related_articles = top_negative[:3] + top_positive[:2]
    # Sort by sentiment (most negative first)
    related_articles.sort(key=lambda x: x["sentiment"])

    key_articles_text = []
    if top_positive:
        key_articles_text.append("Most Positive:")
        for a in top_positive:
            key_articles_text.append(f"  - [{a['source']}] {a['title']} (sentiment: {a['sentiment']:.2f})")
    if top_negative:
        key_articles_text.append("Most Negative:")
        for a in top_negative:
            key_articles_text.append(f"  - [{a['source']}] {a['title']} (sentiment: {a['sentiment']:.2f})")

    # Build prompt
    prompt = config.CHAT_PROMPT.format(
        ticker=ticker,
        date_range=f"{start_date} to {end_date}",
        avg_sentiment=avg_sentiment,
        article_count=article_count,
        trend=trend,
        daily_briefs="\n".join(daily_briefs_text),
        key_articles="\n".join(key_articles_text) if key_articles_text else "No articles available",
        question=question
    )

    # Call Claude
    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

    try:
        message = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=300,
            temperature=0.3,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        answer = message.content[0].text.strip()

        return {
            "answer": answer,
            "related_articles": related_articles[:5]  # Limit to 5
        }

    except Exception as e:
        return {
            "answer": f"Error generating answer: {str(e)}",
            "related_articles": []
        }


if __name__ == "__main__":
    # Test pipeline
    import sys

    ticker = sys.argv[1] if len(sys.argv) > 1 else config.DEFAULT_TICKER
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 7

    print(f"Running pipeline for {ticker} (last {days} days)...")
    results = run_pipeline(ticker, days)
    print("\nResults:")
    print(json.dumps(results, indent=2))
