from __future__ import annotations

from datetime import datetime, timezone

import requests

import database
from config import BOT_AVATAR_URL, BOT_USERNAME, WEBHOOK_URLS


def _send(content: str, key: str) -> None:
    url = WEBHOOK_URLS.get(key)
    if not url:
        print(f"[DIGEST] No webhook for {key}")
        return
    try:
        requests.post(
            url,
            json={"username": BOT_USERNAME, "avatar_url": BOT_AVATAR_URL, "content": content[:2000]},
            timeout=10,
        )
    except Exception as e:
        print(f"[DIGEST] Failed to post digest: {e}")


def _build_digest(is_morning: bool) -> str:
    label = "MORNING BRIEFING" if is_morning else "EVENING WRAP"
    hours = 12 if is_morning else 24
    date_str = datetime.now(timezone.utc).strftime("%d %B %Y")
    stories = database.get_recent_stories(hours=hours)

    if not stories:
        return f"**{label} — {date_str} (IST)**\n\nNo stories in the last {hours} hours."

    # Group by category
    by_cat: dict[str, list[dict]] = {}
    for s in stories:
        by_cat.setdefault(s["category"], []).append(s)

    _LABELS = {
        "india-general": "INDIA",
        "india-politics": "INDIA POLITICS",
        "india-parliament": "PARLIAMENT",
        "india-elections": "ELECTIONS",
        "india-states": "STATES",
        "india-govt-policy": "GOVT & POLICY",
        "india-economy": "ECONOMY",
        "india-markets": "MARKETS",
        "hindu-muslim": "HINDU-MUSLIM",
        "scandals-outrages": "SCANDALS",
        "pak-general": "PAKISTAN",
        "pak-government": "PAK GOVERNMENT",
        "pak-military": "PAK MILITARY",
        "pak-economy": "PAK ECONOMY",
        "geopolitics": "GEOPOLITICS",
        "wars-conflicts": "WARS & CONFLICTS",
        "world-general": "WORLD",
        "global-economy": "GLOBAL ECONOMY",
        "defence": "DEFENCE",
    }

    lines = [f"**{label} — {date_str} (IST)**\n"]
    for cat, label_text in _LABELS.items():
        cat_stories = by_cat.get(cat, [])
        if not cat_stories:
            continue
        lines.append(f"**{label_text}**")
        for s in cat_stories[:4]:
            title = s.get("tweaked_title") or s.get("title", "")
            source = s.get("source", "")
            lines.append(f"• {title} — *{source}*")
        lines.append("")

    content = "\n".join(lines)
    return content[:2000]


def morning_digest() -> None:
    print("[DIGEST] Generating morning digest...")
    content = _build_digest(is_morning=True)
    _send(content, "morning-briefing")
    print("[DIGEST] Morning digest posted.")


def evening_digest() -> None:
    print("[DIGEST] Generating evening digest...")
    content = _build_digest(is_morning=False)
    _send(content, "evening-wrap")
    print("[DIGEST] Evening digest posted.")
