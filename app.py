"""
Investor Sentiment Tracker - Streamlit UI
Simple one-page dashboard for IR teams.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

import config
from db import get_db
from etl import run_pipeline


# ==================== PAGE CONFIG ====================

st.set_page_config(
    page_title="Investor Sentiment Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================== HELPER FUNCTIONS ====================

def validate_environment():
    """Check if all required credentials are set."""
    try:
        config.validate_config()
        return True
    except ValueError as e:
        st.error(f"Configuration Error: {e}")
        st.info("Please set up your API keys in Streamlit secrets or .env file. See README.md for instructions.")
        return False


def get_date_range(option: str) -> tuple:
    """Convert date range option to start/end dates."""
    days = config.DATE_RANGE_OPTIONS.get(option, 7)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")


def render_sentiment_badge(sentiment_score: float) -> str:
    """Return colored badge HTML for sentiment."""
    if sentiment_score >= config.SENTIMENT_THRESHOLDS["positive"]:
        color = "green"
        label = "Positive"
    elif sentiment_score <= config.SENTIMENT_THRESHOLDS["negative"]:
        color = "red"
        label = "Negative"
    else:
        color = "orange"
        label = "Neutral"

    return f'<span style="background-color: {color}; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold;">{label}</span>'


def render_trend_badge(trend: str) -> str:
    """Return colored badge HTML for trend."""
    colors = {
        "improving": "green",
        "stable": "gray",
        "declining": "red"
    }
    color = colors.get(trend, "gray")
    return f'<span style="background-color: {color}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.9em;">{trend.title()}</span>'


# ==================== MAIN APP ====================

def main():
    """Main application logic."""

    # Handle ping requests (for keep-alive)
    if st.query_params.get("ping"):
        st.write("pong")
        st.stop()

    # Validate environment
    if not validate_environment():
        st.stop()

    # Header
    st.title("Investor Sentiment Dashboard")
    st.markdown("AI-powered media sentiment analysis for investor relations")

    # Show welcome message if no data exists
    if "welcomed" not in st.session_state:
        with st.expander("Welcome - Click to get started", expanded=True):
            st.markdown("""
            ### Welcome to Investor Sentiment Dashboard

            This tool helps you monitor how media sentiment toward major tech stocks shifts over time,
            giving you AI-powered insights for investor relations and media monitoring.

            **How to use:**
            1. **Select a company** from the sidebar (TSLA, NVDA, AAPL, GOOGL, or AMZN)
            2. **Choose your date range** and source quality (Major Sources for premium outlets, All Sources for broader coverage)
            3. **Click "Fetch New Articles"** to import and analyze articles with AI
            4. **Explore the dashboard** with daily briefs, sentiment trends, and top topics
            5. **Ask questions** using the AI chatbot to get insights from your data

            **What you'll see:**
            - **Daily IR Briefs**: AI-generated summaries with source links
            - **Sentiment Trends**: Visual charts with 7-day moving averages
            - **Article Volume**: Track media coverage intensity
            - **Top Topics**: Identify emerging themes and narratives

            **Cost & Performance:**
            - Free tier compatible (NewsAPI + Streamlit Cloud)
            - Claude 3.5 Haiku: ~$0.75/month for daily updates
            - ~2 seconds per article for AI analysis

            **Ready?** Choose a company from the sidebar and click "Fetch New Articles" to begin.
            """)

            if st.button("Got it, let's start!", type="primary", use_container_width=True):
                st.session_state.welcomed = True
                st.rerun()

    # ==================== SIDEBAR ====================

    with st.sidebar:
        st.header("Settings")
        st.caption("Configure your sentiment tracking preferences")

        st.markdown("**Company**")
        ticker = st.selectbox(
            "Select company to track",
            options=config.AVAILABLE_TICKERS,
            index=config.AVAILABLE_TICKERS.index(config.DEFAULT_TICKER) if config.DEFAULT_TICKER in config.AVAILABLE_TICKERS else 0,
            key="ticker",
            label_visibility="collapsed"
        )

        st.markdown("**Time Range**")
        date_range_option = st.selectbox(
            "Select date range",
            options=list(config.DATE_RANGE_OPTIONS.keys()),
            index=1,  # Default to "Last 30 days"
            key="date_range_option",
            label_visibility="collapsed"
        )

        st.markdown("**Source Quality**")
        source_quality = st.radio(
            "Select source quality",
            options=list(config.SOURCE_QUALITY_OPTIONS.keys()),
            index=0,  # Default to "Quality (Major Sources)"
            key="source_quality",
            label_visibility="collapsed"
        )

        # Show explanation
        if config.SOURCE_QUALITY_OPTIONS[source_quality] == "quality":
            st.caption("Major US financial sources (WSJ, Bloomberg, Reuters, etc.)")
        else:
            st.caption("All available sources for broader coverage")

        # Show time estimate (varies by source quality)
        days = config.DATE_RANGE_OPTIONS[date_range_option]
        source_filter = config.SOURCE_QUALITY_OPTIONS[source_quality]

        # Quality mode returns fewer articles (~1-2 per day), Quantity mode returns more (~3 per day)
        if source_filter == "quality":
            estimated_articles = min(60, days * 1.5)
        else:
            estimated_articles = min(100, days * 3)

        estimated_time_sec = estimated_articles * 2 + 40  # 2 sec/article + 40 sec overhead
        if estimated_time_sec < 60:
            time_est_display = f"{int(estimated_time_sec)}s"
        else:
            time_est_display = f"{int(round(estimated_time_sec / 60))} min"

        st.caption(f"Est. time: ~{time_est_display} (~{int(estimated_articles)} articles)")

        st.divider()

        if st.button("Fetch New Articles", use_container_width=True, type="primary"):
            # Dynamic status messages
            status_placeholder = st.empty()
            days = config.DATE_RANGE_OPTIONS[date_range_option]

            try:
                import time
                start_time = time.time()

                status_placeholder.info(f"Scanning for financial news... (~20 seconds)")

                from etl import extract_news, analyze_sentiment, create_daily_summary, generate_ir_brief

                # Extract with source filter
                source_filter = config.SOURCE_QUALITY_OPTIONS[source_quality]
                new_articles = extract_news(ticker, days, source_filter=source_filter)

                if not new_articles:
                    check_db = get_db()
                    check_start, check_end = get_date_range(date_range_option)
                    existing = check_db.get_articles_by_date_range(ticker, check_start, check_end)
                    status_placeholder.info(f"Already up to date - {len(existing)} articles in database")
                else:
                    # Analyze (this is the slow part - ~2 sec per article to be conservative)
                    analysis_time_estimate = int(len(new_articles) * 2)
                    if analysis_time_estimate < 60:
                        analysis_time_str = f"~{analysis_time_estimate} seconds"
                    else:
                        analysis_time_str = f"~{int(round(analysis_time_estimate / 60))} minutes"

                    status_placeholder.info(f"Analyzing {len(new_articles)} articles with Claude... ({analysis_time_str})")
                    analyzed_count = 0

                    for i, article in enumerate(new_articles):
                        if i % 10 == 0 and i > 0:
                            # Calculate time remaining
                            elapsed = time.time() - start_time
                            avg_time_per_article = elapsed / i
                            remaining_articles = len(new_articles) - i
                            time_remaining = int(remaining_articles * avg_time_per_article)

                            if time_remaining < 60:
                                time_remaining_str = f"~{time_remaining} seconds left"
                            else:
                                time_remaining_str = f"~{int(round(time_remaining / 60))} minutes left"

                            status_placeholder.info(f"Processing article {i}/{len(new_articles)}... ({time_remaining_str})")

                        sentiment = analyze_sentiment(
                            article_id=article["id"],
                            ticker=ticker,
                            title=article["title"],
                            snippet=article["content_snippet"]
                        )
                        if sentiment:
                            analyzed_count += 1

                    # Summarize (fast - usually < 20 seconds)
                    status_placeholder.info("Generating daily summaries... (~20 seconds)")
                    dates_to_summarize = set()
                    for article in new_articles:
                        pub_date = article["published_at"][:10]
                        dates_to_summarize.add(pub_date)

                    days_summarized = 0
                    for date in dates_to_summarize:
                        summary = create_daily_summary(ticker, date)
                        if summary:
                            days_summarized += 1

                    status_placeholder.success(f"Analyzed {analyzed_count} articles across {days_summarized} days")
                    st.rerun()

            except Exception as e:
                status_placeholder.error(f"Error: {str(e)}")

    # Get date range and fetch data for main view
    start_date, end_date = get_date_range(date_range_option)
    db = get_db()
    daily_data = db.get_daily_agg_range(ticker, start_date, end_date)

    # Show what's currently displayed
    if daily_data:
        dates = [d["date"] for d in daily_data]
        oldest = min(dates)
        newest = max(dates)
        total_articles = sum(d["article_count"] for d in daily_data)
        st.info(f"**Currently displaying:** {ticker} — {len(dates)} days ({oldest} to {newest}) — {total_articles} articles analyzed. Use sidebar to fetch more articles or change date range.")
    else:
        st.info(f"**No data available** for {ticker} in selected date range — Click 'Fetch New Articles' in the sidebar to import data")

    # ==================== Q&A CHATBOT ====================

    st.subheader("Ask Questions About Sentiment")
    st.markdown("Get AI-powered insights from Claude based on your imported articles. Ask about trends, concerns, or specific topics.")

    if not daily_data:
        st.info("Fetch articles first to enable Q&A")
    else:
        col_input, col_button = st.columns([5, 1])

        with col_input:
            question = st.text_input(
                "Your question",
                placeholder="e.g., What are investors most worried about? Why did sentiment drop?",
                key="chat_question",
                label_visibility="collapsed"
            )

        with col_button:
            ask_button = st.button("Ask", type="primary", use_container_width=True)

        if ask_button and question:
            with st.spinner("Analyzing sentiment data..."):
                from etl import answer_sentiment_question
                result = answer_sentiment_question(ticker, question, start_date, end_date)

            # Display answer
            st.markdown(
                f"""
                <div style="background-color: var(--background-color);
                            border: 1px solid var(--secondary-background-color);
                            padding: 20px;
                            border-radius: 8px;
                            border-left: 4px solid #3b82f6;
                            margin-top: 12px;
                            margin-bottom: 20px;">
                    <p style="margin: 0; font-size: 1em; line-height: 1.7; color: var(--text-color);">{result['answer']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Display related articles
            if result.get('related_articles'):
                st.markdown("**Most relevant articles:**")
                for article in result['related_articles']:
                    sentiment_badge = "NEGATIVE" if article['sentiment'] < -0.3 else "POSITIVE" if article['sentiment'] > 0.3 else "NEUTRAL"
                    badge_color = "#ef4444" if article['sentiment'] < -0.3 else "#10b981" if article['sentiment'] > 0.3 else "#f59e0b"

                    st.markdown(
                        f"<span style='background-color: {badge_color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75em; font-weight: bold;'>{sentiment_badge}</span> "
                        f"[{article['source']}] [{article['title']}]({article['url']}) ({article['date']})",
                        unsafe_allow_html=True
                    )

            # Show context disclaimer
            articles = db.get_articles_by_date_range(ticker, start_date, end_date)
            st.caption(f"Based on {len(articles)} articles from {start_date} to {end_date}")

        elif ask_button and not question:
            st.warning("Please enter a question")

    st.divider()

    if not daily_data:
        # Check if ANY data exists for this ticker (look back 1 year)
        from datetime import datetime
        one_year_ago = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        all_data = db.get_daily_agg_range(ticker, one_year_ago, end_date)

        if all_data:
            # User has some data, but not for the selected range
            dates = [d["date"] for d in all_data]
            oldest_date = min(dates)
            newest_date = max(dates)
            days_available = len(dates)

            st.warning(
                f"**Data range mismatch**\n\n"
                f"You have **{days_available} days** of data for {ticker} ({oldest_date} to {newest_date}), "
                f"but selected **'{date_range_option}'**.\n\n"
                f"Click **'Fetch New Articles'** to get more data, or select a shorter date range."
            )
        else:
            # No data at all for this ticker
            st.info(
                f"**No data yet for {ticker}**\n\n"
                f"Click **'Fetch New Articles'** to get started."
            )
        st.stop()

    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(daily_data)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    # ==================== 2x2 CHARTS GRID ====================

    # Standard height for all grid elements
    GRID_HEIGHT = 350

    # Top row: Daily IR Brief | Sentiment Trend
    col_left, col_right = st.columns([1, 1], gap="medium")

    with col_left:
        st.subheader("Daily IR Brief")

        # Navigation: Dropdown + Prev/Next buttons
        col_prev, col_dropdown, col_next = st.columns([1, 4, 1])

        # Initialize session state for selected index if not exists, or reset if out of bounds
        if "brief_date_idx" not in st.session_state or st.session_state.brief_date_idx >= len(df):
            st.session_state.brief_date_idx = len(df) - 1

        with col_prev:
            if st.button("←", use_container_width=True, disabled=(st.session_state.brief_date_idx == 0)):
                st.session_state.brief_date_idx -= 1
                st.rerun()

        with col_dropdown:
            # Create options for dropdown
            date_options = {i: f"{df.iloc[i]['date'].strftime('%b %d, %Y')} ({df.iloc[i]['article_count']} articles)"
                           for i in range(len(df))}

            # Ensure index is valid
            safe_index = min(st.session_state.brief_date_idx, len(df) - 1)

            selected_date_idx = st.selectbox(
                "Select date",
                options=list(date_options.keys()),
                index=safe_index,
                format_func=lambda x: date_options[x],
                label_visibility="collapsed",
                key="brief_dropdown"
            )

            # Update session state when dropdown changes
            if selected_date_idx != st.session_state.brief_date_idx:
                st.session_state.brief_date_idx = selected_date_idx
                st.rerun()

        with col_next:
            if st.button("→", use_container_width=True, disabled=(st.session_state.brief_date_idx == len(df) - 1)):
                st.session_state.brief_date_idx += 1
                st.rerun()

        selected_row = df.iloc[st.session_state.brief_date_idx]
        selected_date_str = selected_row['date'].strftime('%Y-%m-%d')

        # Get articles for this specific date (need to add time to ensure we catch the full day)
        start_datetime = f"{selected_date_str}T00:00:00"
        end_datetime = f"{selected_date_str}T23:59:59"

        # Query by the specific date range
        result = db.client.table("articles")\
            .select("*, mentions!inner(*)")\
            .eq("mentions.company_ticker", ticker)\
            .gte("published_at", start_datetime)\
            .lte("published_at", end_datetime)\
            .order("published_at", desc=False)\
            .execute()

        daily_articles = result.data

        # Build sources HTML
        sources_html = ""
        if daily_articles:
            sources_html = '<div style="border-top: 1px solid var(--secondary-background-color); padding-top: 12px; margin-top: 12px;"><p style="font-size: 0.85em; font-weight: 600; color: var(--text-color); opacity: 0.8; margin-bottom: 8px;">SOURCES:</p>'

            for article in daily_articles:
                mention = article.get("mentions", [{}])[0] if article.get("mentions") else {}
                sentiment_score = mention.get('sentiment_score', 0) if mention else 0
                sentiment_badge = "POS" if sentiment_score > 0.3 else "NEG" if sentiment_score < -0.3 else "NEU"
                badge_color = "#10b981" if sentiment_score > 0.3 else "#ef4444" if sentiment_score < -0.3 else "#64748b"

                sources_html += f'<div style="margin-bottom: 6px;"><span style="background-color: {badge_color}; color: white; padding: 1px 6px; border-radius: 3px; font-size: 0.7em; font-weight: bold;">{sentiment_badge}</span> <a href="{article["url"]}" target="_blank" style="font-size: 0.85em; color: #3b82f6; text-decoration: none;">{article["source"]}: {article["title"][:60]}...</a></div>'

            sources_html += '</div>'

        # Display brief card with fixed height including sources
        st.markdown(
            f"""
            <div style="background-color: var(--background-color);
                        border: 1px solid var(--secondary-background-color);
                        padding: 20px;
                        border-radius: 8px;
                        border-left: 4px solid #3b82f6;
                        height: {GRID_HEIGHT - 60}px;
                        overflow-y: auto;">
                <h4 style="margin-top: 0; color: var(--text-color);">{selected_row['date'].strftime('%B %d, %Y')}</h4>
                <p style="margin-bottom: 16px;">{render_sentiment_badge(selected_row['avg_sentiment'])} {render_trend_badge(selected_row['sentiment_trend'])} <span style="color: var(--text-color); opacity: 0.7; font-size: 0.85em;">{selected_row['article_count']} articles</span></p>
                <p style="font-size: 0.95em; line-height: 1.7; color: var(--text-color); margin-bottom: 16px;">{selected_row['ir_brief']}</p>
                {sources_html}
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_right:
        st.subheader("Sentiment Trend")

        fig = go.Figure()

        # Add 7-day moving average if enough data
        if len(df) >= 7:
            df["ma7"] = df["avg_sentiment"].rolling(window=7, min_periods=1).mean()
            fig.add_trace(go.Scatter(
                x=df["date"],
                y=df["ma7"],
                mode="lines",
                name="7-day avg",
                line=dict(color="#94a3b8", width=2, dash="dash"),
                hovertemplate="<b>%{x|%Y-%m-%d}</b><br>7-day avg: %{y:.2f}<extra></extra>"
            ))

        # Add sentiment line
        fig.add_trace(go.Scatter(
            x=df["date"],
            y=df["avg_sentiment"],
            mode="lines+markers",
            name="Daily Sentiment",
            line=dict(color="#3b82f6", width=3),
            marker=dict(size=8, color="#3b82f6"),
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Sentiment: %{y:.2f}<extra></extra>"
        ))

        # Add zero line
        fig.add_hline(y=0, line_dash="dot", line_color="#64748b", opacity=0.5, line_width=1)

        # Add threshold zones
        fig.add_hrect(
            y0=config.SENTIMENT_THRESHOLDS["positive"], y1=1.0,
            fillcolor="#10b981", opacity=0.08, line_width=0
        )
        fig.add_hrect(
            y0=config.SENTIMENT_THRESHOLDS["negative"], y1=-1.0,
            fillcolor="#ef4444", opacity=0.08, line_width=0
        )

        fig.update_layout(
            yaxis_title="Sentiment Score",
            yaxis_range=[-1.0, 1.0],
            hovermode="x unified",
            height=GRID_HEIGHT,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=10, r=10, t=30, b=40),
            template="plotly_white",
            font=dict(family="Inter, system-ui, sans-serif", size=12)
        )

        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128, 128, 128, 0.2)")
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128, 128, 128, 0.2)")

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Bottom row: Article Volume | Top Topics
    col_left2, col_right2 = st.columns([1, 1], gap="medium")

    with col_left2:
        st.subheader("Article Volume")

        fig2 = go.Figure()

        fig2.add_trace(go.Bar(
            x=df["date"],
            y=df["article_count"],
            marker_color="#8b5cf6",
            marker_line_width=0,
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Articles: %{y}<extra></extra>"
        ))

        fig2.update_layout(
            yaxis_title="Number of Articles",
            height=GRID_HEIGHT,
            showlegend=False,
            margin=dict(l=10, r=10, t=10, b=40),
            template="plotly_white",
            font=dict(family="Inter, system-ui, sans-serif", size=12)
        )

        fig2.update_xaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128, 128, 128, 0.2)")
        fig2.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128, 128, 128, 0.2)")

        st.plotly_chart(fig2, use_container_width=True)

    with col_right2:
        st.subheader("Top Topics")

        # Get all mentions for the date range and count raw topics
        all_topics = []
        articles = db.get_articles_by_date_range(ticker, start_date, end_date)

        for article in articles:
            if article.get("mentions"):
                for mention in article["mentions"]:
                    if mention.get("key_topics"):
                        all_topics.extend(mention["key_topics"])

        if all_topics:
            topic_counts = pd.Series(all_topics).value_counts().head(8)
            # Sort so highest is at top
            topic_counts = topic_counts.sort_values(ascending=True)

            fig3 = go.Figure(go.Bar(
                x=topic_counts.values,
                y=topic_counts.index,
                orientation='h',
                marker_color='#06b6d4',
                marker_line_width=0,
                hovertemplate="<b>%{y}</b><br>Mentions: %{x}<extra></extra>"
            ))

            fig3.update_layout(
                xaxis_title="Mentions",
                yaxis_title="",
                height=GRID_HEIGHT,
                showlegend=False,
                margin=dict(l=10, r=10, t=10, b=40),
                template="plotly_white",
                font=dict(family="Inter, system-ui, sans-serif", size=12)
            )

            fig3.update_xaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128, 128, 128, 0.2)")
            fig3.update_yaxes(showgrid=False)

            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No topics available for this date range.")

    # ==================== RECENT ARTICLES TABLE ====================

    with st.expander("Recent Articles", expanded=False):
        articles = db.get_articles_by_date_range(ticker, start_date, end_date)

        if articles:
            # Prepare table data
            table_data = []
            for article in articles[:20]:  # Limit to 20
                mention = article.get("mentions", [{}])[0] if article.get("mentions") else {}

                table_data.append({
                    "Date": article["published_at"][:10],
                    "Source": article["source"],
                    "Title": article["title"],
                    "URL": article["url"],
                    "Sentiment": f"{mention.get('sentiment_score', 0):.2f}" if mention else "N/A",
                    "Label": mention.get("sentiment_label", "N/A").title() if mention else "N/A"
                })

            articles_df = pd.DataFrame(table_data)

            # Display as interactive table
            st.dataframe(
                articles_df,
                column_config={
                    "URL": st.column_config.LinkColumn("URL"),
                    "Sentiment": st.column_config.NumberColumn("Sentiment", format="%.2f"),
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No articles available.")

    # ==================== FOOTER ====================

    st.divider()
    st.caption("**Data Sources:** NewsAPI (newsapi.org) | **Sentiment Analysis:** Claude 3.5 Haiku by Anthropic")
    st.caption("**Technical Implementation:** Built by Nicolo Pastrone with Python and Streamlit. Integrated Anthropic's Claude 3.5 Haiku API for cost-efficient sentiment analysis with custom prompt engineering. Supabase handles PostgreSQL database storage with automatic deduplication. NewsAPI provides real-time article feeds with configurable source filtering. Developed collaboratively with Claude Code, demonstrating modern AI-assisted development workflows.")


# ==================== ENTRY POINT ====================

if __name__ == "__main__":
    main()
