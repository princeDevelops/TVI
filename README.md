# The Verdict India — Discord News Bot

A self-hosted news aggregator that fetches articles from 35+ RSS feeds, 11 YouTube channels, and optional news APIs every 30 minutes. Each article is processed by Groq AI (LLaMA 3.3-70B), then posted as a rich Discord embed to categorized channels. Runs entirely via GitHub Actions — no server required.

---

## How it works

```
GitHub Actions (every 30 min)
  └─ fetch RSS + YouTube feeds
  └─ filter already-seen articles (SQLite)
  └─ scrape article body + OG image
  └─ Groq AI → rewritten headline, summary, confidence
  └─ POST Discord embeds to category channels + #queue
  └─ commit seen_articles.db back to repo
```

Morning (7 AM IST) and evening (8 PM IST) digests are posted automatically to dedicated channels.

---

## Setup

### 1. Fork and clone

```bash
git clone https://github.com/YOUR_USERNAME/theverdictindia.git
cd theverdictindia
```

### 2. Install dependencies (for local testing)

```bash
pip install -r news_bot/requirements.txt
```

### 3. Create your Discord server and channels

Create a Discord server with these channels (names are suggestions — you can rename them):

| Channel | Purpose |
|---|---|
| `#queue` | All articles (unified feed for review) |
| `#india-general` | General India news |
| `#india-politics` | Political news |
| `#india-parliament` | Parliament coverage |
| `#india-elections` | Election news |
| `#india-govt-policy` | Government policy |
| `#india-economy` | Economy |
| `#india-states` | State-level news |
| `#hindu-muslim` | Communal/religious news |
| `#scandals-outrages` | Scandals and crime |
| `#pak-general` | Pakistan general |
| `#pak-government` | Pakistan government |
| `#pak-military` | Pakistan military |
| `#pak-economy` | Pakistan economy |
| `#geopolitics` | International relations |
| `#wars-conflicts` | Wars and conflicts |
| `#world-general` | World news |
| `#india-markets` | Stock markets |
| `#global-economy` | Global economy |
| `#defence` | Defence news |
| `#youtube` | YouTube video uploads |
| `#api-news` | News from API sources |
| `#morning-briefing` | Daily morning digest |
| `#evening-wrap` | Daily evening digest |
| `#bot-logs` | Run summaries |
| `#errors` | Error alerts |
| `#feed-health` | Feed status reports |

For each channel: **Channel Settings → Integrations → Webhooks → New Webhook → Copy Webhook URL**

### 4. Add secrets to GitHub

Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**.

Add all of the following:

```
GROQ_API_KEY          # from console.groq.com (free tier works)

WEBHOOK_QUEUE
WEBHOOK_INDIA_GENERAL
WEBHOOK_INDIA_POLITICS
WEBHOOK_INDIA_PARLIAMENT
WEBHOOK_INDIA_ELECTIONS
WEBHOOK_INDIA_GOVT_POLICY
WEBHOOK_INDIA_ECONOMY
WEBHOOK_INDIA_STATES
WEBHOOK_HINDU_MUSLIM
WEBHOOK_SCANDALS_OUTRAGES
WEBHOOK_PAK_GENERAL
WEBHOOK_PAK_GOVERNMENT
WEBHOOK_PAK_MILITARY
WEBHOOK_PAK_ECONOMY
WEBHOOK_GEOPOLITICS
WEBHOOK_WARS_CONFLICTS
WEBHOOK_WORLD_GENERAL
WEBHOOK_INDIA_MARKETS
WEBHOOK_GLOBAL_ECONOMY
WEBHOOK_DEFENCE
WEBHOOK_YOUTUBE
WEBHOOK_API_NEWS
WEBHOOK_GOOGLE_ALERTS
WEBHOOK_MORNING_BRIEFING
WEBHOOK_EVENING_WRAP
WEBHOOK_BOT_LOGS
WEBHOOK_ERRORS
WEBHOOK_FEED_HEALTH
```

**Optional** (bot works fine without these):
```
NEWSAPI_KEY     # newsapi.org
GNEWS_KEY       # gnews.io
CURRENTS_KEY    # currentsapi.services
```

### 5. Enable GitHub Actions

Go to your repo → **Actions tab** → click **"I understand my workflows, go ahead and enable them"** if prompted.

### 6. Test immediately

Go to **Actions → News Bot → Run workflow** and click the green button. Watch the run — it should complete in under 5 minutes. Check your Discord channels for embeds.

### 7. It runs automatically

The workflow is scheduled via cron (`*/30 * * * *`) and fires every 30 minutes automatically. GitHub Actions may delay runs by a few minutes — this is normal.

---

## Local testing

```bash
cp news_bot/.env.example news_bot/.env
# Fill in at minimum GROQ_API_KEY and WEBHOOK_BOT_LOGS

cd theverdictindia
python news_bot/main.py
```

---

## Adding new RSS feeds

Open [news_bot/config.py](news_bot/config.py) and append to the `FEEDS` list:

```python
{
    "name": "Display Name",          # shown in Discord embed author
    "url":  "https://example.com/rss.xml",
    "category": "india-general",     # must be a key in CATEGORY_LABELS
    "type": "rss",                   # or "youtube"
},
```

**Valid category keys:**
`india-general` · `india-politics` · `india-parliament` · `india-elections` ·
`india-govt-policy` · `india-economy` · `india-states` · `hindu-muslim` ·
`scandals-outrages` · `pak-general` · `pak-government` · `pak-military` ·
`pak-economy` · `geopolitics` · `wars-conflicts` · `world-general` ·
`india-markets` · `global-economy` · `defence` · `youtube` · `api-news`

---

## Database persistence

SQLite (`news_bot/seen_articles.db`) is used to deduplicate articles across runs.

Because GitHub Actions is stateless (a fresh VM each time), the DB is **committed back to the repository** at the end of every run with the message `chore: update seen_articles DB [skip ci]`. The `[skip ci]` tag prevents the commit from triggering another workflow run.

This means:
- The DB grows in the repo over time (small — a few MB after months)
- If you need to reset seen articles, delete the DB file and push
- The DB is safe to commit — it contains only URLs, titles, and timestamps (no secrets)

---

## Architecture notes

- **No discord.py bot client** — Discord webhooks are stateless HTTP POSTs, perfect for GitHub Actions. No bot token, no persistent connection needed.
- **Groq rate limits** — The bot adds 1s delay between Groq calls and caps at 30 articles per run. Groq free tier allows ~30 req/min on LLaMA 3.3-70B.
- **Error isolation** — Every feed, scrape, AI call, and webhook POST is individually wrapped in try/except. One bad article never kills the run.
- **Digest timing** — Digests trigger if the bot runs within ±14 minutes of 01:30 UTC (7 AM IST) or 14:30 UTC (8 PM IST). Given the 30-minute schedule, at most one run will trigger each digest per day.
