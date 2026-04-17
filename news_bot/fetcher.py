from __future__ import annotations

import feedparser
import requests
from datetime import datetime, timezone
from typing import Optional

import config
import database

_RSS_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0; +https://github.com)"}


# ── helpers ────────────────────────────────────────────────────────────────────

def _parse_published(entry) -> datetime:
    for attr in ("published_parsed", "updated_parsed"):
        val = getattr(entry, attr, None)
        if val:
            try:
                return datetime(*val[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return datetime.now(timezone.utc)


def _extract_video_id(entry, url: str) -> str:
    vid = getattr(entry, "yt_videoid", "") or ""
    if vid:
        return vid
    if "v=" in url:
        return url.split("v=")[-1].split("&")[0]
    if "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    return ""


# ── per-feed fetch functions ───────────────────────────────────────────────────

def fetch_rss_feed(feed_cfg: dict) -> tuple[list[dict], bool]:
    try:
        parsed = feedparser.parse(feed_cfg["url"], request_headers=_RSS_HEADERS)
        if parsed.bozo and not parsed.entries:
            return [], False

        articles: list[dict] = []
        for entry in parsed.entries[:20]:
            title = (entry.get("title") or "").strip()
            url = (entry.get("link") or "").strip()
            if not title or not url:
                continue
            description = (
                entry.get("summary") or entry.get("description") or ""
            ).strip()
            articles.append(
                {
                    "title": title,
                    "url": url,
                    "description": description,
                    "published": _parse_published(entry),
                    "source": feed_cfg["name"],
                    "category": feed_cfg["category"],
                    "type": "rss",
                }
            )
        return articles, True

    except Exception as e:
        print(f"[FETCHER] RSS error for {feed_cfg['name']}: {e}")
        return [], False


def fetch_youtube_feed(feed_cfg: dict) -> tuple[list[dict], bool]:
    try:
        parsed = feedparser.parse(feed_cfg["url"], request_headers=_RSS_HEADERS)
        if parsed.bozo and not parsed.entries:
            return [], False

        articles: list[dict] = []
        for entry in parsed.entries[:10]:
            title = (entry.get("title") or "").strip()
            url = (entry.get("link") or "").strip()
            if not title or not url:
                continue

            video_id = _extract_video_id(entry, url)

            description = (
                getattr(entry, "media_description", None)
                or entry.get("summary")
                or ""
            )

            articles.append(
                {
                    "title": title,
                    "url": url,
                    "description": (description or "").strip(),
                    "published": _parse_published(entry),
                    "source": feed_cfg["name"],
                    "category": "youtube",
                    "type": "youtube",
                    "video_id": video_id,
                    "thumbnail_url": (
                        f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                        if video_id
                        else None
                    ),
                }
            )
        return articles, True

    except Exception as e:
        print(f"[FETCHER] YouTube error for {feed_cfg['name']}: {e}")
        return [], False


# ── API sources ────────────────────────────────────────────────────────────────

def _budget_ok(service: str) -> bool:
    used = database.api_calls_today(service)
    cap = config.API_DAILY_CAPS.get(service, 0)
    if used >= cap:
        print(
            f"[FETCHER] {service} daily budget exhausted ({used}/{cap}). Skipping."
        )
        return False
    return True


def fetch_newsapi() -> list[dict]:
    if not config.NEWSAPI_KEY:
        return []
    if not _budget_ok("newsapi"):
        return []
    try:
        resp = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={
                "q": "India OR Pakistan",
                "language": "en",
                "pageSize": 20,
                "apiKey": config.NEWSAPI_KEY,
            },
            timeout=10,
        )
        database.record_api_call("newsapi")
        if resp.status_code != 200:
            print(f"[FETCHER] NewsAPI returned {resp.status_code}")
            return []
        articles = []
        for item in resp.json().get("articles", []):
            url = item.get("url", "")
            if not url or url == "[Removed]":
                continue
            articles.append(
                {
                    "title": (item.get("title") or "").strip(),
                    "url": url,
                    "description": (item.get("description") or "").strip(),
                    "published": datetime.now(timezone.utc),
                    "source": item.get("source", {}).get("name", "NewsAPI"),
                    "category": "api-news",
                    "type": "api",
                }
            )
        return articles
    except Exception as e:
        print(f"[FETCHER] NewsAPI error: {e}")
        return []


def fetch_gnews() -> list[dict]:
    if not config.GNEWS_KEY:
        return []
    if not _budget_ok("gnews"):
        return []
    try:
        resp = requests.get(
            "https://gnews.io/api/v4/top-headlines",
            params={"country": "in", "lang": "en", "max": 20, "token": config.GNEWS_KEY},
            timeout=10,
        )
        database.record_api_call("gnews")
        if resp.status_code != 200:
            print(f"[FETCHER] GNews returned {resp.status_code}")
            return []
        articles = []
        for item in resp.json().get("articles", []):
            url = item.get("url", "")
            if not url:
                continue
            articles.append(
                {
                    "title": (item.get("title") or "").strip(),
                    "url": url,
                    "description": (item.get("description") or "").strip(),
                    "published": datetime.now(timezone.utc),
                    "source": item.get("source", {}).get("name", "GNews"),
                    "category": "api-news",
                    "type": "api",
                }
            )
        return articles
    except Exception as e:
        print(f"[FETCHER] GNews error: {e}")
        return []


def fetch_currents() -> list[dict]:
    if not config.CURRENTS_KEY:
        return []
    if not _budget_ok("currents"):
        return []
    try:
        resp = requests.get(
            "https://api.currentsapi.services/v1/latest-news",
            params={"language": "en", "country": "IN", "apiKey": config.CURRENTS_KEY},
            timeout=10,
        )
        database.record_api_call("currents")
        if resp.status_code != 200:
            print(f"[FETCHER] Currents returned {resp.status_code}")
            return []
        articles = []
        for item in resp.json().get("news", []):
            url = item.get("url", "")
            if not url:
                continue
            articles.append(
                {
                    "title": (item.get("title") or "").strip(),
                    "url": url,
                    "description": (item.get("description") or "").strip(),
                    "published": datetime.now(timezone.utc),
                    "source": item.get("author") or "Currents",
                    "category": "api-news",
                    "type": "api",
                }
            )
        return articles
    except Exception as e:
        print(f"[FETCHER] Currents error: {e}")
        return []


# ── main entry point ──────────────────────────────────────────────────────────

def fetch_all_feeds() -> tuple[list[dict], dict[str, dict]]:
    all_articles: list[dict] = []
    feed_health: dict[str, dict] = {}

    for feed_cfg in config.FEEDS:
        if feed_cfg["type"] == "youtube":
            articles, ok = fetch_youtube_feed(feed_cfg)
        else:
            articles, ok = fetch_rss_feed(feed_cfg)

        feed_health[feed_cfg["name"]] = {"success": ok, "count": len(articles)}
        all_articles.extend(articles)

    return all_articles, feed_health
