import json
import random
import re
import time

from groq import Groq

import config

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=config.GROQ_API_KEY)
    return _client


_SYSTEM_PROMPT = """\
You are two things at once, and you must do both in a single JSON response.

ROLE 1 - News Analyst:
You are a sharp political analyst specializing in Indian and Pakistani politics, \
South Asian geopolitics, and world affairs. You return structured JSON only. \
No markdown, no explanation, no code blocks. Raw JSON only.

ROLE 2 - X (Twitter) Content Strategist:
You write high-engagement posts for an informed Indian audience. \
Your posts interpret the news, never just report it. \
Every post must answer the "so what?" for the reader. \
Voice: Smart Brevity. No fluff. No opener phrases like "In a world where" or "Today we see". \
Hard rules that cannot be broken under any circumstances:
- Zero emojis. Not one. Not even a flag.
- Zero m-dashes (the -- or the unicode dash character). Use a colon or period instead.
- Never start with "According to [Source]". Credit the source naturally at the end, e.g. "via Dawn" or "via Reuters".
- Never use "BREAKING", "Must Read", or "Thread" unless impact_score is 9 or 10.
- Maximum 2 sentences before the bullet points or closing question.
- If confidence is unverified, open with "Unverified:" and explain why it still matters."""

_X_FORMAT_INSTRUCTIONS = {
    "impact": """\
Use the IMPACT format:
[Insightful headline reframe, 1-2 sentences] + [2-3 bullet points on the ripple effect, each under 15 words] + [One closing question to drive replies]. \
The question must be specific, not generic like "What do you think?".""",

    "contrarian": """\
Use the CONTRARIAN format:
[State the news in one sentence] + [One short paragraph explaining why the common interpretation might be wrong or incomplete] + [A direct call to action, e.g. "Disagree? Here is why you should reconsider."].""",

    "historical": """\
Use the HISTORICAL format:
[State the news in one sentence] + [One sentence drawing a specific parallel to a past event with year and outcome] + [One sentence on what that precedent suggests will happen next].""",
}


_USER_TEMPLATE = """\
Analyze this news article and return ONLY a raw JSON object.

Source: {source}
Category: {category}
Original Title: {title}
Description: {description}
Article Body: {body}

For the x_post field, {x_format_instruction}

Return this exact JSON:
{{
  "tweaked_title": "<Rewrite the headline in your own words. Identical meaning, different wording. Max 120 chars.>",
  "summary_points": ["<point 1>", "<point 2>", "<point 3>"],
  "why_it_matters": "<Concrete 1-2 sentence implication. Specific about who is affected and how. No vague language.>",
  "confidence": "<confirmed | developing | unverified>",
  "category_refined": "<Same category string passed in, or corrected if clearly wrong. Only valid channel keys.>",
  "flag": "<most relevant country flag emoji>",
  "impact_score": <integer 1-10, where 10 is a history-changing event>,
  "x_post": "<The complete ready-to-post X content. No emojis. No m-dashes. Source credited at end.>"
}}"""


def process_article(
    title: str,
    description: str,
    body: str | None,
    source: str,
    category: str,
) -> dict:
    fallback = {
        "tweaked_title": title,
        "summary_points": ["Could not process with AI."],
        "why_it_matters": "",
        "confidence": "unverified",
        "category_refined": category,
        "flag": "🌐",
        "impact_score": 5,
        "x_post": "",
    }

    x_format_key = random.choice(["impact", "contrarian", "historical"])
    x_format_instruction = _X_FORMAT_INSTRUCTIONS[x_format_key]

    user_prompt = _USER_TEMPLATE.format(
        source=source,
        category=category,
        title=title,
        description=description or "Not available",
        body=body or "Not available",
        x_format_instruction=x_format_instruction,
    )

    try:
        response = _get_client().chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.5,
            max_tokens=900,
        )
        raw = response.choices[0].message.content.strip()

        # Strip accidental markdown fences
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        result = json.loads(raw)

        # Validate category; reject hallucinated values
        if result.get("category_refined") not in config.VALID_CATEGORIES:
            result["category_refined"] = category

        result.setdefault("tweaked_title", title)
        result.setdefault("summary_points", ["No summary available."])
        result.setdefault("why_it_matters", "")
        result.setdefault("confidence", "unverified")
        result.setdefault("flag", "🌐")
        result.setdefault("impact_score", 5)
        result.setdefault("x_post", "")

        # Enforce hard rules as a post-processing safety net
        x = result["x_post"]
        x = re.sub(r"\u2014|\u2013|--", " ", x)   # remove all dash variants
        x = re.sub(r"[^\x00-\x7F\u0900-\u097F\s]", "", x)  # strip non-ASCII except Devanagari
        result["x_post"] = x.strip()

        # Store which format was used so poster can label it
        result["x_format"] = x_format_key

        time.sleep(config.GROQ_DELAY)
        return result

    except Exception as e:
        print(f"[PROCESSOR] Groq error for '{title[:60]}': {e}")
        time.sleep(config.GROQ_DELAY)
        return fallback
