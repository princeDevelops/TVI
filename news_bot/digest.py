from __future__ import annotations

import json
from datetime import datetime, timezone

import requests
from groq import Groq, RateLimitError as GroqRateLimitError
import google.generativeai as genai

import config
import database
from config import BOT_AVATAR_URL, BOT_USERNAME, WEBHOOK_URLS

_groq_client: Groq | None = None
_gemini_ready: bool = False


def _get_groq() -> Groq:
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=config.GROQ_API_KEY)
    return _groq_client


def _get_gemini() -> bool:
    global _gemini_ready
    if not _gemini_ready and config.GEMINI_API_KEY:
        genai.configure(api_key=config.GEMINI_API_KEY)
        _gemini_ready = True
    return _gemini_ready


def _send_digest(content: str, is_morning: bool) -> None:
    key = "morning-briefing" if is_morning else "evening-wrap"
    url = WEBHOOK_URLS.get(key)
    if not url:
        print(f"[DIGEST] No webhook configured for {key}")
        return
    try:
        requests.post(
            url,
            json={
                "username": BOT_USERNAME,
                "avatar_url": BOT_AVATAR_URL,
                "content": content[:2000],
            },
            timeout=10,
        )
    except Exception as e:
        print(f"[DIGEST] Failed to post digest: {e}")


def _generate_digest(stories: list[dict], is_morning: bool) -> str:
    if not stories:
        label = "🌅 MORNING" if is_morning else "🌆 EVENING"
        date_str = datetime.now(timezone.utc).strftime("%d %B %Y")
        return f"**{label} BRIEFING — {date_str} (IST)**\n\n*No stories available.*"

    date_str = datetime.now(timezone.utc).strftime("%d %B %Y")
    label = "🌅 MORNING" if is_morning else "🌆 EVENING"

    stories_json = json.dumps(stories[:40], ensure_ascii=False, default=str)

    user_prompt = f"""Write a news digest from these stories. Format exactly as shown:

**{label} BRIEFING — {date_str} (IST)**

🇮🇳 **INDIA**
[3-4 bullet points, most important India stories]

🇵🇰 **PAKISTAN**
[2-3 bullet points]

🌍 **WORLD**
[2-3 bullet points]

📊 **ECONOMY**
[1-2 bullet points]

🔍 **TO WATCH**
[The single most important developing story and why]

Stories: {stories_json}

Rules: Under 1800 chars total. Specific facts only. No filler words."""

    system = "You are a senior political news editor for an Indian audience."

    # Try Groq first
    if config.GROQ_API_KEY:
        try:
            response = _get_groq().chat.completions.create(
                model=config.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.4,
                max_tokens=700,
            )
            return response.choices[0].message.content.strip()
        except GroqRateLimitError:
            print("[DIGEST] Groq rate limit hit, falling back to Gemini.")
        except Exception as e:
            print(f"[DIGEST] Groq error: {e}")

    # Fall back to Gemini
    if _get_gemini():
        try:
            model = genai.GenerativeModel(
                model_name=config.GEMINI_MODEL,
                system_instruction=system,
            )
            response = model.generate_content(
                user_prompt,
                generation_config=genai.GenerationConfig(temperature=0.4, max_output_tokens=700),
            )
            return response.text.strip()
        except Exception as e:
            print(f"[DIGEST] Gemini error: {e}")

    return f"**{label} BRIEFING — {date_str} (IST)**\n\n*Digest generation failed. Check bot logs.*"


def morning_digest() -> None:
    print("[DIGEST] Generating morning digest...")
    stories = database.get_recent_stories(hours=12)
    content = _generate_digest(stories, is_morning=True)
    _send_digest(content, is_morning=True)
    print(f"[DIGEST] Morning digest posted ({len(stories)} stories).")


def evening_digest() -> None:
    print("[DIGEST] Generating evening digest...")
    stories = database.get_recent_stories(hours=24)
    content = _generate_digest(stories, is_morning=False)
    _send_digest(content, is_morning=False)
    print(f"[DIGEST] Evening digest posted ({len(stories)} stories).")
