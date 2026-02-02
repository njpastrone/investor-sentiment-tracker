# Collaborating with Claude on This Project

Instructions for AI-assisted development of the Company Signals Tracker.

## Project Philosophy

- **Simple over clever**: Readable code, minimal abstractions
- **Minimal files**: 4 core files (app.py, etl.py, db.py, config.py)
- **Ship then improve**: Get MVP working, add categories later
- **Cost-conscious**: Use Haiku, cache everything, batch operations

## File Ownership

| File | Responsibility | Never Put Here |
|------|---------------|----------------|
| `app.py` | UI only - Streamlit components, layout | Business logic, API calls |
| `etl.py` | Data pipeline - fetch, classify, transform | Database queries, UI code |
| `db.py` | Database operations - CRUD, queries | External API calls, UI code |
| `config.py` | Constants, settings, prompts | Logic, functions with side effects |

## Key Constraints

Always keep in mind:

1. **Free tier compatible**: Streamlit Cloud, Supabase free, no paid APIs except Claude
2. **1000 company scale**: Design for hundreds of companies, not millions
3. **Single user**: No auth, no multi-tenancy
4. **Daily batch**: Not real-time, overnight refresh is fine
5. **Claude Haiku only**: Don't upgrade to Sonnet unless necessary

## Working with Claude

### Good Requests

```
"Add CSV upload to app.py for importing company watchlist"

"Update etl.py to fetch from Google News RSS instead of NewsAPI"

"Add a relevance_score filter to the dashboard, minimum 0.5"
```

### Better Requests

```
"Add CSV upload to app.py for importing companies.
Columns: name, ticker (optional).
Skip duplicates by ticker.
Show count of added/skipped."
```

### If Claude Over-Engineers

Remind:
- "This is an MVP - keep it simple"
- "No new files unless absolutely necessary"
- "We can add that feature later"
- "Does this work on Streamlit free tier?"

## Common Tasks

### Add a Company to Watchlist
1. Insert into `companies` table via `db.py`
2. No other files need changes

### Modify the AI Prompt
1. Edit prompt in `config.py`
2. Test with 3-5 sample articles
3. Check output parsing in `etl.py` still works

### Change Dashboard Layout
1. Edit `app.py` only
2. Keep single-page structure
3. Test on narrow viewport (mobile width)

### Add a New Signal Category
1. Update prompt in `config.py` to return category
2. Update `signals` table schema in `db.py`
3. Add filter dropdown in `app.py`

## Prompt Templates

Keep prompts in `config.py` with these guidelines:

- **Temperature 0.0-0.3** for consistent classification
- **Max 500 tokens output** to control costs
- **JSON output** for reliable parsing
- **Few-shot examples** if classification is inconsistent

## Database Conventions

- Use `uuid` for primary keys
- Use `created_at` timestamp on all tables
- Use `active` boolean for soft deletes
- Deduplicate articles by URL (unique constraint)

## Cost Monitoring

After changes that affect API usage:
```
"Estimate the new monthly Claude API cost"
```

Target: **Under $5/month** for 1000 companies.

## Deployment

### First Deploy Checklist
- [ ] All secrets in `.streamlit/secrets.toml`
- [ ] `requirements.txt` complete
- [ ] Database tables created (init script or auto-create)
- [ ] No hardcoded paths

### Secrets Required
```toml
ANTHROPIC_API_KEY = "sk-..."
SUPABASE_URL = "https://xxx.supabase.co"
SUPABASE_KEY = "eyJ..."
```

## Anti-Patterns

**Avoid**:
- Separate folders for 4 files
- Real-time processing (batch is fine)
- Complex caching (simple dedup by URL is enough)
- Multiple AI models (Haiku for everything)
- Enterprise features (auth, teams, audit logs)

**Instead**:
- Flat file structure
- Daily batch jobs
- URL-based deduplication
- Single model, tune prompts
- Single user, simple permissions

## Testing Approach

- **Manual testing first**: This is an MVP
- **Test with 5-10 companies**: Before scaling to 100+
- **Check Claude output**: Log raw responses during development
- **Verify deduplication**: Same article shouldn't appear twice

## Getting Unstuck

If something isn't working:

1. Check Streamlit logs in browser console
2. Add `st.write(variable)` for debugging
3. Test Claude prompts in the API playground first
4. Check Supabase dashboard for data issues

## Version Control

- Commit after each working feature
- Use descriptive commit messages
- Don't commit `.streamlit/secrets.toml`
- Keep `requirements.txt` updated
