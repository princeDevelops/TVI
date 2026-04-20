import os
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URLS = {
    "queue":             os.getenv("WEBHOOK_QUEUE"),
    "india-general":     os.getenv("WEBHOOK_INDIA_GENERAL"),
    "india-politics":    os.getenv("WEBHOOK_INDIA_POLITICS"),
    "india-parliament":  os.getenv("WEBHOOK_INDIA_PARLIAMENT"),
    "india-elections":   os.getenv("WEBHOOK_INDIA_ELECTIONS"),
    "india-govt-policy": os.getenv("WEBHOOK_INDIA_GOVT_POLICY"),
    "india-economy":     os.getenv("WEBHOOK_INDIA_ECONOMY"),
    "india-states":      os.getenv("WEBHOOK_INDIA_STATES"),
    "hindu-muslim":      os.getenv("WEBHOOK_HINDU_MUSLIM"),
    "scandals-outrages": os.getenv("WEBHOOK_SCANDALS_OUTRAGES"),
    "pak-general":       os.getenv("WEBHOOK_PAK_GENERAL"),
    "pak-government":    os.getenv("WEBHOOK_PAK_GOVERNMENT"),
    "pak-military":      os.getenv("WEBHOOK_PAK_MILITARY"),
    "pak-economy":       os.getenv("WEBHOOK_PAK_ECONOMY"),
    "geopolitics":       os.getenv("WEBHOOK_GEOPOLITICS"),
    "wars-conflicts":    os.getenv("WEBHOOK_WARS_CONFLICTS"),
    "world-general":     os.getenv("WEBHOOK_WORLD_GENERAL"),
    "india-markets":     os.getenv("WEBHOOK_INDIA_MARKETS"),
    "global-economy":    os.getenv("WEBHOOK_GLOBAL_ECONOMY"),
    "defence":           os.getenv("WEBHOOK_DEFENCE"),
    "brics":             os.getenv("WEBHOOK_BRICS"),
    "youtube":           os.getenv("WEBHOOK_YOUTUBE"),
    "api-news":          os.getenv("WEBHOOK_API_NEWS"),
    "google-alerts":     os.getenv("WEBHOOK_GOOGLE_ALERTS"),
    "morning-briefing":  os.getenv("WEBHOOK_MORNING_BRIEFING"),
    "evening-wrap":      os.getenv("WEBHOOK_EVENING_WRAP"),
    "bot-logs":          os.getenv("WEBHOOK_BOT_LOGS"),
    "errors":            os.getenv("WEBHOOK_ERRORS"),
    "breaking-alerts":   os.getenv("WEBHOOK_BREAKING_ALERTS"),
    "feed-health":       os.getenv("WEBHOOK_FEED_HEALTH"),
}

CATEGORY_LABELS = {
    "india-general":     "India General",
    "india-politics":    "India Politics",
    "india-parliament":  "India Parliament",
    "india-elections":   "India Elections",
    "india-govt-policy": "India Govt & Policy",
    "india-economy":     "India Economy",
    "india-states":      "India States",
    "hindu-muslim":      "Hindu-Muslim",
    "scandals-outrages": "Scandals & Outrages",
    "pak-general":       "Pakistan General",
    "pak-government":    "Pakistan Government",
    "pak-military":      "Pakistan Military",
    "pak-economy":       "Pakistan Economy",
    "geopolitics":       "Geopolitics",
    "wars-conflicts":    "Wars & Conflicts",
    "world-general":     "World General",
    "india-markets":     "India Markets",
    "global-economy":    "Global Economy",
    "defence":           "Defence",
    "brics":             "BRICS",
    "youtube":           "YouTube",
    "api-news":          "API News",
    "google-alerts":     "Google Alerts",
}

VALID_CATEGORIES = set(CATEGORY_LABELS.keys())

FEEDS = [
    # ── India ──────────────────────────────────────────────────────────────
    {
        "name": "NDTV India",
        "url": "https://feeds.feedburner.com/ndtvnews-india-news",
        "category": "india-general",
        "type": "rss",
    },
    {
        "name": "NDTV Politics",
        "url": "https://www.ndtv.com/rss/politics",
        "category": "india-politics",
        "type": "rss",
    },
    {
        "name": "NDTV World",
        "url": "https://feeds.feedburner.com/ndtvnews-world-news",
        "category": "world-general",
        "type": "rss",
    },
    {
        "name": "NDTV Crime",
        "url": "https://www.ndtv.com/rss/crime",
        "category": "scandals-outrages",
        "type": "rss",
    },
    {
        "name": "NDTV Business",
        "url": "https://www.ndtv.com/rss/business",
        "category": "india-economy",
        "type": "rss",
    },
    {
        "name": "The Hindu National",
        "url": "https://www.thehindu.com/news/national/feeder/default.rss",
        "category": "india-general",
        "type": "rss",
    },
    {
        "name": "The Hindu International",
        "url": "https://www.thehindu.com/news/international/feeder/default.rss",
        "category": "geopolitics",
        "type": "rss",
    },
    {
        "name": "The Hindu Business",
        "url": "https://www.thehindu.com/business/feeder/default.rss",
        "category": "india-markets",
        "type": "rss",
    },
    {
        "name": "Times of India",
        "url": "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",
        "category": "india-general",
        "type": "rss",
    },
    {
        "name": "Indian Express India",
        "url": "https://indianexpress.com/section/india/feed/",
        "category": "india-general",
        "type": "rss",
    },
    {
        "name": "Indian Express World",
        "url": "https://indianexpress.com/section/world/feed/",
        "category": "world-general",
        "type": "rss",
    },
    {
        "name": "Indian Express Business",
        "url": "https://indianexpress.com/section/business/feed/",
        "category": "global-economy",
        "type": "rss",
    },
    {
        "name": "News18 India",
        "url": "https://www.news18.com/rss/india.xml",
        "category": "india-general",
        "type": "rss",
    },
    {
        "name": "News18 Politics",
        "url": "https://www.news18.com/rss/politics.xml",
        "category": "india-politics",
        "type": "rss",
    },
    {
        "name": "Economic Times Top",
        "url": "https://economictimes.indiatimes.com/rssfeedsdefault.cms",
        "category": "india-economy",
        "type": "rss",
    },
    {
        "name": "Economic Times Economy",
        "url": "https://economictimes.indiatimes.com/news/economy/rssfeeds/1373380680.cms",
        "category": "india-economy",
        "type": "rss",
    },
    {
        "name": "Economic Times Politics",
        "url": "https://economictimes.indiatimes.com/news/politics-and-nation/rssfeeds/1052732854.cms",
        "category": "india-govt-policy",
        "type": "rss",
    },
    {
        "name": "LiveMint",
        "url": "https://www.livemint.com/rss/news",
        "category": "india-markets",
        "type": "rss",
    },
    {
        "name": "ANI News",
        "url": "https://www.aninews.in/rss/world.xml",
        "category": "india-general",
        "type": "rss",
    },
    {
        "name": "Reuters India",
        "url": "https://ir.thomsonreuters.com/rss/news-releases.xml",
        "category": "india-general",
        "type": "rss",
    },
    {
        "name": "Reuters India Business",
        "url": "https://www.reuters.com/rssFeed/businessNews",
        "category": "india-markets",
        "type": "rss",
    },
    {
        "name": "OpIndia",
        "url": "https://www.opindia.com/feed/",
        "category": "hindu-muslim",
        "type": "rss",
    },
    {
        "name": "Swarajya",
        "url": "https://swarajyamag.com/feed",
        "category": "hindu-muslim",
        "type": "rss",
    },
    # ── Pakistan ───────────────────────────────────────────────────────────
    {
        "name": "Dawn",
        "url": "https://www.dawn.com/feeds/home",
        "category": "pak-general",
        "type": "rss",
    },
    {
        "name": "ARY News",
        "url": "https://arynews.tv/feed/",
        "category": "pak-general",
        "type": "rss",
    },
    {
        "name": "Geo TV",
        "url": "https://geo.tv/rss/top-stories",
        "category": "pak-general",
        "type": "rss",
    },
    {
        "name": "The News International",
        "url": "https://www.thenews.com.pk/rss/1/1",
        "category": "pak-general",
        "type": "rss",
    },
    {
        "name": "Express Tribune",
        "url": "https://tribune.com.pk/feed/",
        "category": "pak-general",
        "type": "rss",
    },
    {
        "name": "Samaa English",
        "url": "https://www.samaaenglish.tv/feed/",
        "category": "pak-general",
        "type": "rss",
    },
    # ── World / Geopolitics ────────────────────────────────────────────────
    {
        "name": "BBC World",
        "url": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "category": "world-general",
        "type": "rss",
    },
    {
        "name": "Reuters Top",
        "url": "https://www.reuters.com/rssFeed/topNews",
        "category": "geopolitics",
        "type": "rss",
    },
    {
        "name": "Al Jazeera",
        "url": "https://www.aljazeera.com/xml/rss/all.xml",
        "category": "geopolitics",
        "type": "rss",
    },
    {
        "name": "The Defense Post",
        "url": "https://www.thedefensepost.com/feed/",
        "category": "defence",
        "type": "rss",
    },
    {
        "name": "The Print Defence",
        "url": "https://theprint.in/category/defence/feed/",
        "category": "defence",
        "type": "rss",
    },
    {
        "name": "Livefist Defence",
        "url": "https://www.livefist.com/feeds/posts/default",
        "category": "defence",
        "type": "rss",
    },
    {
        "name": "Indian Defence Review",
        "url": "https://www.indiandefencereview.com/feed/",
        "category": "defence",
        "type": "rss",
    },
    # ── Geopolitics ────────────────────────────────────────────────────────
    {
        "name": "The Diplomat",
        "url": "https://thediplomat.com/feed/",
        "category": "geopolitics",
        "type": "rss",
    },
    {
        "name": "ORF India",
        "url": "https://www.orfonline.org/feed/",
        "category": "geopolitics",
        "type": "rss",
    },
    {
        "name": "Firstpost World",
        "url": "https://www.firstpost.com/rss/world.xml",
        "category": "geopolitics",
        "type": "rss",
    },
    # ── BRICS ──────────────────────────────────────────────────────────────
    {
        "name": "TASS English",
        "url": "https://tass.com/rss/v2.xml",
        "category": "brics",
        "type": "rss",
    },
    {
        "name": "Global Times",
        "url": "https://www.globaltimes.cn/rss/outbrain.xml",
        "category": "brics",
        "type": "rss",
    },
    {
        "name": "Daily Maverick SA",
        "url": "https://www.dailymaverick.co.za/feed/",
        "category": "brics",
        "type": "rss",
    },
    # ── Google Alerts ──────────────────────────────────────────────────────
    {
        "name": "Google Alerts",
        "url": "https://www.google.co.in/alerts/feeds/16192332283874439099/16393250519301350627",
        "category": "google-alerts",
        "type": "rss",
    },
    # ── YouTube ────────────────────────────────────────────────────────────
    {
        "name": "NDTV India YT",
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCZFMm1mMw0F81Z37aaEzTUA",
        "category": "youtube",
        "type": "youtube",
    },
    {
        "name": "NDTV YT",
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCF57Pkzuv7s9wWr8WBFxqHg",
        "category": "youtube",
        "type": "youtube",
    },
    {
        "name": "Aaj Tak YT",
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCt4t-jeY85JegMlZ-E5UWtA",
        "category": "youtube",
        "type": "youtube",
    },
    {
        "name": "India Today YT",
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCYPvAwZP8pZhSMW8qs7cVCw",
        "category": "youtube",
        "type": "youtube",
    },
    {
        "name": "Zee News YT",
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCNFiGAWBKJy6BTOX2CWXlJA",
        "category": "youtube",
        "type": "youtube",
    },
    {
        "name": "News18 YT",
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCGMbAGABL4NKEEkfWB86Hxg",
        "category": "youtube",
        "type": "youtube",
    },
    {
        "name": "ET Now YT",
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UC9Ptj4RKeXS2sPXN0OEZP5Q",
        "category": "youtube",
        "type": "youtube",
    },
    {
        "name": "WION YT",
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UC5kwgFNic8JcGhHvJPgGTuQ",
        "category": "youtube",
        "type": "youtube",
    },
    {
        "name": "ABP News YT",
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCCJDDM2acgkKQoh0hPX7VRQ",
        "category": "youtube",
        "type": "youtube",
    },
    {
        "name": "Times Now YT",
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UC5xJH2lDL4KM1vfXbCeXbrg",
        "category": "youtube",
        "type": "youtube",
    },
    {
        "name": "Republic TV YT",
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCbGBpVbQMDxFBqM7VrFYgfA",
        "category": "youtube",
        "type": "youtube",
    },
]


NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
GNEWS_KEY = os.getenv("GNEWS_KEY")
CURRENTS_KEY = os.getenv("CURRENTS_KEY")

# Daily API call budgets — 95% of each service's hard limit (5% buffer).
# 48 runs/day at every-30-min schedule.
# Currents: 1000 limit → 950 usable → ~19/run headroom (1 call/run = well within budget)
# GNews:    100  limit →  95 usable →  ~1/run headroom (1 call/run = exactly on budget)
# NewsAPI:  100  limit →  95 usable →  ~1/run headroom (1 call/run = exactly on budget)
API_DAILY_CAPS = {
    "currents": 950,
    "gnews":    95,
    "newsapi":  95,
}

MAX_ARTICLES_PER_RUN = 50
ARTICLE_DELAY = 0.5
WEBHOOK_DELAY = 0.5
GROQ_DELAY = 1.0

BOT_USERNAME = "NewsRoom Bot"
BOT_AVATAR_URL = "https://i.imgur.com/4M34hi2.png"
