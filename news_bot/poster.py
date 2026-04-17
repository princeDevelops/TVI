from __future__ import annotations

import re
import time
from datetime import datetime, timezone

import requests

import config
from config import (
    BOT_AVATAR_URL,
    BOT_USERNAME,
    CATEGORY_LABELS,
    WEBHOOK_DELAY,
    WEBHOOK_URLS,
)

def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&quot;", '"', text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


_CONFIDENCE_COLORS = {
    "confirmed":  3066993,
    "developing": 16750848,
    "unverified": 15158332,
}

_CONFIDENCE_EMOJIS = {
    "confirmed":  "🟢",
    "developing": "🟡",
    "unverified": "🔴",
}


# ── utilities ──────────────────────────────────────────────────────────────────

def _time_ago(published: datetime | None) -> str:
    if published is None:
        return "Unknown time"
    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)
    diff = datetime.now(timezone.utc) - published
    seconds = int(diff.total_seconds())
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        m = seconds // 60
        return f"{m} min{'s' if m != 1 else ''} ago"
    if seconds < 86400:
        h = seconds // 3600
        return f"{h} hr{'s' if h != 1 else ''} ago"
    if seconds < 172800:
        return "Yesterday"
    return f"{seconds // 86400} days ago"


def _published_iso(published: datetime | None) -> str | None:
    if published is None:
        return None
    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)
    return published.isoformat()


def _post_webhook(webhook_url: str | None, payload: dict) -> bool:
    if not webhook_url:
        return False
    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        time.sleep(WEBHOOK_DELAY)
        if resp.status_code not in (200, 204):
            _log_error(
                f"Webhook returned {resp.status_code}: {resp.text[:200]}"
            )
            return False
        return True
    except Exception as e:
        _log_error(f"Webhook POST exception: {e}")
        return False


def _log_error(message: str) -> None:
    error_url = WEBHOOK_URLS.get("errors")
    if not error_url:
        print(f"[ERROR] {message}")
        return
    try:
        requests.post(
            error_url,
            json={"content": f"⚠️ `{message[:1900]}`"},
            timeout=10,
        )
    except Exception:
        print(f"[ERROR] {message}")


# ── public functions ───────────────────────────────────────────────────────────

def post_article(article: dict, ai_result: dict) -> None:
    if article.get("type") == "youtube":
        _post_youtube(article)
        return

    category = ai_result.get("category_refined") or article.get("category", "world-general")
    tweaked_title = ai_result.get("tweaked_title") or article["title"]
    summary_points = ai_result.get("summary_points") or []
    why_it_matters = ai_result.get("why_it_matters") or ""
    confidence = ai_result.get("confidence", "unverified")
    flag = ai_result.get("flag", "🌐")

    color = _CONFIDENCE_COLORS.get(confidence, _CONFIDENCE_COLORS["unverified"])
    conf_emoji = _CONFIDENCE_EMOJIS.get(confidence, "🔴")
    category_label = CATEGORY_LABELS.get(category, category)

    published = article.get("published")
    time_ago_str = _time_ago(published)
    ts = _published_iso(published)

    raw_desc = _strip_html((article.get("description") or "").strip())
    body_text = _strip_html((article.get("body") or "").strip())
    summary_str = (
        "\n".join(f"• {p}" for p in summary_points) if summary_points else "• Not available"
    )
    x_post = ai_result.get("x_post", "").strip()
    x_format = ai_result.get("x_format", "")
    impact_score = ai_result.get("impact_score", 5)

    _X_FORMAT_LABELS = {"impact": "Impact", "contrarian": "Contrarian", "historical": "Historical"}
    x_label = _X_FORMAT_LABELS.get(x_format, "Insight")

    def _field(name: str, value: str) -> dict:
        return {"name": name, "value": value[:1024] or "\u200b", "inline": False}

    # Body goes in description (4096 char limit) — stays as one unbroken block
    body_section = body_text[:4000] if body_text else "*Body not available for this source.*"

    fields = []
    fields.append(_field("📰 Original Headline", article["title"]))
    if raw_desc:
        fields.append(_field("📄 RSS Description", raw_desc[:1024]))
    fields.append(_field("💡 AI Summary", summary_str))
    fields.append(_field("📌 Why It Matters", why_it_matters or "*Not available.*"))
    if x_post:
        x_value = f"```\n{x_post[:980]}\n```"
        fields.append(_field(f"X Post [{x_label}] • Impact {impact_score}/10", x_value))

    embed: dict = {
        "color": color,
        "author": {
            "name": f"{flag}  {category_label.upper()}  •  {article['source']}  •  {time_ago_str}"
        },
        "title": tweaked_title[:256],
        "url": article["url"],
        "description": f"**📖 Article Body**\n{body_section}",
        "fields": fields,
        "footer": {
            "text": (
                f"{conf_emoji} {confidence.capitalize()} • 🤖 llama-3.3-70b"
            )
        },
    }
    if ts:
        embed["timestamp"] = ts
    image_url = article.get("image_url")
    if image_url:
        embed["image"] = {"url": image_url}

    payload = {
        "username": BOT_USERNAME,
        "avatar_url": BOT_AVATAR_URL,
        "embeds": [embed],
    }

    # Post to category channel then queue
    _post_webhook(WEBHOOK_URLS.get(category), payload)
    _post_webhook(WEBHOOK_URLS.get("queue"), payload)


def _post_youtube(article: dict) -> None:
    video_id = article.get("video_id") or ""
    thumbnail = article.get("thumbnail_url") or (
        f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg" if video_id else None
    )
    description = (article.get("description") or "")[:300]
    if len(article.get("description") or "") > 300:
        description += "..."

    published = article.get("published")
    ts = _published_iso(published)

    embed: dict = {
        "color": 16711680,
        "author": {"name": f"▶️ {article['source']}"},
        "title": article["title"][:256],
        "url": article["url"],
        "description": (
            f"**▶️ New video uploaded**\n\n"
            f"{description or '*No description available.*'}"
        ),
        "footer": {
            "text": f"📺 YouTube • {article['source']} • 🕐 {_time_ago(published)}"
        },
    }
    if ts:
        embed["timestamp"] = ts
    if thumbnail:
        embed["image"] = {"url": thumbnail}

    payload = {
        "username": BOT_USERNAME,
        "avatar_url": BOT_AVATAR_URL,
        "embeds": [embed],
    }

    _post_webhook(WEBHOOK_URLS.get("youtube"), payload)
    _post_webhook(WEBHOOK_URLS.get("queue"), payload)


def post_feed_health(feed_health: dict, total_new: int) -> None:
    webhook_url = WEBHOOK_URLS.get("feed-health")
    if not webhook_url:
        return

    failed = [n for n, info in feed_health.items() if not info["success"]]
    zero = [n for n, info in feed_health.items() if info["success"] and info["count"] == 0]
    succeeded = len(feed_health) - len(failed)

    lines = [
        f"**📊 Feed Health — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}**",
        f"New articles posted: **{total_new}**",
        f"Feeds OK: **{succeeded}/{len(feed_health)}**",
    ]
    if failed:
        lines.append(f"\n❌ **Failed ({len(failed)}):**")
        lines += [f"• {n}" for n in failed[:20]]
    if zero:
        lines.append(f"\n⚠️ **Zero items ({len(zero)}):**")
        lines += [f"• {n}" for n in zero[:20]]

    content = "\n".join(lines)
    if len(content) > 1900:
        content = content[:1897] + "..."
    _post_webhook(webhook_url, {"content": content})


def post_log(message: str) -> None:
    webhook_url = WEBHOOK_URLS.get("bot-logs")
    if not webhook_url:
        print(f"[LOG] {message}")
        return
    try:
        requests.post(
            webhook_url,
            json={"content": f"📋 {message[:1900]}"},
            timeout=10,
        )
    except Exception:
        print(f"[LOG] {message}")


def post_error(message: str) -> None:
    _log_error(message)
