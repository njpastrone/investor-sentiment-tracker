# Collaborating with Claude on This Project

This document explains how to work with Claude Code to build and maintain the Investor Sentiment Tracker.

## Project Philosophy

- **Beginner-friendly**: Readable code over clever tricks
- **Minimal**: Prefer fewer files, less duplication
- **Autonomous**: Claude makes sensible defaults, asks only when critical
- **Cost-conscious**: Cache API calls, sample data, use short prompts

## Working with Claude

### When Adding Features

**Good Request**:
> "Add a 7-day moving average line to the sentiment chart"

**Better Request**:
> "Add a 7-day moving average to the sentiment chart in app.py. Use Plotly's built-in smoothing. Update only the chart section."

### When Debugging

**Always provide**:
1. Error message (full traceback)
2. What you were trying to do
3. Relevant file location

**Example**:
> "Getting KeyError: 'sentiment' in etl.py line 45 when running analyze_sentiment(). Claude response was: [paste response]"

### Key Constraints to Remind Claude

If Claude suggests something complex, remind:
- "Keep it simple - this is an MVP"
- "Must work on Streamlit free tier"
- "Minimize Claude API calls"
- "Don't create new files unless necessary"

## File Ownership

- `app.py` - UI only, no business logic
- `etl.py` - All data processing and API calls
- `db.py` - Database queries only, no external calls
- `config.py` - Constants and settings, no logic

## Common Tasks

### Add New Data Source

1. Add API credentials to `config.py`
2. Create extraction function in `etl.py`
3. Update database schema in `db.py` if needed
4. Wire into UI in `app.py`

### Modify Claude Prompts

1. Update prompt template in `etl.py`
2. Test with 3-5 sample articles
3. Verify JSON parsing works
4. Check token usage (aim for <500 tokens/article)

### Change UI Layout

1. Edit `app.py` only
2. Keep single-page structure
3. Test on mobile width (Streamlit Cloud default)

## Deployment Checklist

Before asking Claude to prepare deployment:
- [ ] All API keys moved to Streamlit secrets
- [ ] No hardcoded paths (use relative paths)
- [ ] `requirements.txt` updated
- [ ] Database initialization runs on first launch
- [ ] Error handling for missing API keys

## Cost Monitoring

After changes, ask Claude:
> "Estimate the new daily Claude API cost based on these changes"

Target: <$5/month for single-company tracking.

## Getting Help

### From Claude

**Research requests**:
> "Find the best free alternative to NewsAPI with longer history"

**Code review**:
> "Review etl.py for redundant API calls or missing error handling"

**Optimization**:
> "Suggest 3 ways to reduce Claude API costs without losing accuracy"

### From Documentation

- Streamlit deployment: [docs.streamlit.io](https://docs.streamlit.io/)
- Claude API: [docs.anthropic.com](https://docs.anthropic.com/)
- NewsAPI: [newsapi.org/docs](https://newsapi.org/docs)

## Version Control with Claude

When making significant changes:
1. Ask Claude to summarize changes first
2. Review before committing
3. Use descriptive commit messages

**Example workflow**:
> "I want to add Reddit sentiment. First, outline the changes to each file, then implement."

## Anti-Patterns

**Avoid asking Claude to**:
- Create separate folders for 3 files
- Add enterprise features (auth, multi-tenancy)
- Optimize before it works
- Write extensive documentation for internal functions

**Instead**:
- Keep flat structure until 10+ files
- Build for single user first
- Make it work, then optimize
- Document only public interfaces

## Success Criteria

You should be able to:
1. Explain what every file does in one sentence
2. Deploy in under 10 minutes
3. Debug issues by reading error messages
4. Add a new data source in under 1 hour

If something feels too complex, it probably is. Ask Claude to simplify.
