from __future__ import annotations

import re
import time
from datetime import datetime, timezone

import requests

from config import (
    BOT_AVATAR_URL,
    BOT_USERNAME,
    CATEGORY_LABELS,
    WEBHOOK_DELAY,
    WEBHOOK_URLS,
)

_CATEGORY_COLORS = {
    "india-general":     2067276,
    "india-politics":    3447003,
    "india-parliament":  1752220,
    "india-elections":   10181046,
    "india-states":      3066993,
    "india-govt-policy": 2123412,
    "india-economy":     15844367,
    "india-markets":     16776960,
    "hindu-muslim":      15158332,
    "scandals-outrages": 10038562,
    "pak-general":       1146986,
    "pak-government":    3447003,
    "pak-military":      7419530,
    "pak-economy":       15844367,
    "geopolitics":       9807270,
    "wars-conflicts":    15158332,
    "world-general":     8311585,
    "global-economy":    16750848,
    "defence":           4886754,
    "brics":             16744272,
    "youtube":           16711680,
    "api-news":          8421504,
}


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&quot;", '"', text)
    return re.sub(r"\s+", " ", text).strip()


def _time_ago(published: datetime | None) -> str:
    if published is None:
        return "Unknown time"
    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)
    diff = datetime.now(timezone.utc) - published
    s = int(diff.total_seconds())
    if s < 60:
        return "just now"
    if s < 3600:
        m = s // 60
        return f"{m} min{'s' if m != 1 else ''} ago"
    if s < 86400:
        h = s // 3600
        return f"{h} hr{'s' if h != 1 else ''} ago"
    if s < 172800:
        return "Yesterday"
    return f"{s // 86400} days ago"


def _published_iso(published: datetime | None) -> str | None:
    if published is None:
        return None
    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)
    return published.isoformat()


def _post_webhook(url: str | None, payload: dict) -> bool:
    if not url:
        return False
    try:
        resp = requests.post(url, json=payload, timeout=10)
        time.sleep(WEBHOOK_DELAY)
        if resp.status_code not in (200, 204):
            _log_error(f"Webhook {resp.status_code}: {resp.text[:200]}")
            return False
        return True
    except Exception as e:
        _log_error(f"Webhook POST failed: {e}")
        return False


def _log_error(message: str) -> None:
    url = WEBHOOK_URLS.get("errors")
    if not url:
        print(f"[ERROR] {message}")
        return
    try:
        requests.post(url, json={"content": f"⚠️ `{message[:1900]}`"}, timeout=10)
    except Exception:
        print(f"[ERROR] {message}")


def post_article(article: dict) -> None:
    if article.get("type") == "youtube":
        _post_youtube(article)
        return

    category = article.get("category", "world-general")
    color = _CATEGORY_COLORS.get(category, 8421504)
    category_label = CATEGORY_LABELS.get(category, category)

    published = article.get("published")
    time_ago_str = _time_ago(published)
    ts = _published_iso(published)

    raw_desc = _strip_html((article.get("description") or ""))
    body_text = _strip_html((article.get("body") or ""))

    def _field(name: str, value: str) -> dict:
        return {"name": name, "value": value[:1024] or "\u200b", "inline": False}

    fields = []
    if raw_desc:
        fields.append(_field("📄 Description", raw_desc[:1024]))

    embed: dict = {
        "color": color,
        "author": {
            "name": f"{category_label.upper()}  •  {article['source']}  •  {time_ago_str}"
        },
        "title": article["title"][:256],
        "url": article["url"],
        "description": f"**📖 Article Body**\n{body_text[:4000]}" if body_text else None,
        "fields": fields,
        "footer": {"text": f"📰 {article['source']}"},
    }

    # Remove description key entirely if empty to avoid Discord rejecting null
    if not embed["description"]:
        del embed["description"]

    if ts:
        embed["timestamp"] = ts
    if article.get("image_url"):
        embed["image"] = {"url": article["image_url"]}

    payload = {"username": BOT_USERNAME, "avatar_url": BOT_AVATAR_URL, "embeds": [embed]}

    _post_webhook(WEBHOOK_URLS.get(category), payload)
    _post_webhook(WEBHOOK_URLS.get("queue"), payload)


def _post_youtube(article: dict) -> None:
    video_id = article.get("video_id") or ""
    thumbnail = article.get("thumbnail_url") or (
        f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg" if video_id else None
    )
    description = _strip_html((article.get("description") or ""))[:300]

    published = article.get("published")
    ts = _published_iso(published)

    embed: dict = {
        "color": 16711680,
        "author": {"name": f"▶️  {article['source']}  •  {_time_ago(published)}"},
        "title": article["title"][:256],
        "url": article["url"],
        "description": f"**▶️ New video**\n\n{description or '*No description.*'}",
        "footer": {"text": f"📺 YouTube • {article['source']}"},
    }
    if ts:
        embed["timestamp"] = ts
    if thumbnail:
        embed["image"] = {"url": thumbnail}

    payload = {"username": BOT_USERNAME, "avatar_url": BOT_AVATAR_URL, "embeds": [embed]}
    _post_webhook(WEBHOOK_URLS.get("youtube"), payload)
    _post_webhook(WEBHOOK_URLS.get("queue"), payload)


def post_feed_health(feed_health: dict, total_new: int) -> None:
    url = WEBHOOK_URLS.get("feed-health")
    if not url:
        return
    failed = [n for n, i in feed_health.items() if not i["success"]]
    zero = [n for n, i in feed_health.items() if i["success"] and i["count"] == 0]
    ok = len(feed_health) - len(failed)
    lines = [
        f"**Feed Health — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}**",
        f"New articles posted: **{total_new}** | Feeds OK: **{ok}/{len(feed_health)}**",
    ]
    if failed:
        lines += [f"\n❌ **Failed ({len(failed)}):**"] + [f"• {n}" for n in failed[:20]]
    if zero:
        lines += [f"\n⚠️ **Zero items ({len(zero)}):**"] + [f"• {n}" for n in zero[:20]]
    content = "\n".join(lines)[:1900]
    _post_webhook(url, {"content": content})


def post_log(message: str) -> None:
    url = WEBHOOK_URLS.get("bot-logs")
    if not url:
        print(f"[LOG] {message}")
        return
    try:
        requests.post(url, json={"content": f"📋 {message[:1900]}"}, timeout=10)
    except Exception:
        print(f"[LOG] {message}")


def post_breaking_alert(article: dict) -> None:
    """Posts a high-visibility embed to #breaking-alerts for watchlist articles."""
    url = WEBHOOK_URLS.get("breaking-alerts")
    if not url:
        return

    published = article.get("published")
    ts = _published_iso(published)

    embed: dict = {
        "color": 15158332,  # bright red
        "author": {"name": f"BREAKING  •  {article.get('source', '')}  •  {_time_ago(published)}"},
        "title": article["title"][:256],
        "url": article["url"],
        "footer": {"text": f"NewsRoom Bot • Breaking Alert"},
    }
    if ts:
        embed["timestamp"] = ts
    if article.get("image_url"):
        embed["image"] = {"url": article["image_url"]}

    payload = {
        "username": BOT_USERNAME,
        "avatar_url": BOT_AVATAR_URL,
        "content": "@everyone",
        "embeds": [embed],
    }
    _post_webhook(url, payload)


def post_error(message: str) -> None:
    _log_error(message)
