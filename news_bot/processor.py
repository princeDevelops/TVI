from __future__ import annotations

import json
import re
import time

from groq import Groq, RateLimitError as GroqRateLimitError
import google.generativeai as genai

import config

# ── clients (lazy-initialised) ─────────────────────────────────────────────────

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


# ── prompts ────────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are two things at once, and you must do both in a single JSON response.

ROLE 1 - News Analyst:
You are a sharp political analyst specializing in Indian and Pakistani politics, \
South Asian geopolitics, and world affairs. You return structured JSON only. \
No markdown, no explanation, no code blocks. Raw JSON only.

ROLE 2 - Expert Digital Journalist and X (Twitter) Growth Specialist:
You transform raw news into high-engagement X posts that bypass aggregator detection \
by adding unique context, analysis, and a "why it matters" angle for an informed Indian audience.

X POST HARD RULES — never break these:
- Zero emojis. Not one. Not even a flag.
- Zero m-dashes (unicode or --). Use a colon or period instead.
- Zero all-caps words.
- No hashtags unless highly specific (e.g. #Budget2026). No generic tags.
- Never start with "Breaking News", "Check this out", "According to reports", or any generic lead-in.
- Never use "BREAKING", "Must Read", or "Thread".
- Source credit at the end as "via [Source Name]" on its own line.
- Target length: under 280 characters. Never exceed 300.
- If confidence is unverified, start Line 1 with "Unverified:" and explain why it still matters.

X POST STRUCTURE — use exactly four lines plus a footer:
Line 1 — The Hook: A bold statement or the single most important fact. Start directly with the core insight.
Line 2 — The Insight: The secondary implication or a specific data point that most people will miss.
Line 3 — The Context: How this connects to a larger ongoing trend. Add the curator's voice, not just the facts.
Line 4 — The Question: A human-centric question that prompts replies, not retweets. Make it specific to this story.
Footer — "via [Source Name]" on its own line."""

_CATEGORY_GUIDE = """\
Read the article content carefully and assign the single best matching category:

india-general      = India news that does not fit a more specific category below
india-politics     = Indian party politics, political leaders, BJP/Congress/AAP/TMC moves
india-parliament   = Lok Sabha, Rajya Sabha, parliamentary sessions, bills passing, MPs, Speaker
india-elections    = Election results, voting, EVMs, campaign trail, seat projections, EC rulings
india-states       = State government news, Chief Ministers, state legislation, governor's rule
india-govt-policy  = Central government schemes, ministry orders, regulatory policy, ordinances
india-economy      = India macro economy, GDP, RBI, inflation, fiscal deficit, budget
india-markets      = BSE/NSE, Sensex/Nifty, IPOs, stocks, mutual funds, FII flows
hindu-muslim       = Communal relations, temple/mosque disputes, conversion, religious violence
scandals-outrages  = Corruption, scams, arrests of public figures, controversies, crimes by elites
pak-general        = Pakistan news that does not fit a more specific category below
pak-government     = Pakistan PM, cabinet, Parliament, PPP/PML-N/PTI governance
pak-military       = Pakistan Army, COAS, ISI, military courts, civil-military relations
pak-economy        = Pakistan economy, IMF bailout, rupee, inflation, CPEC, debt
geopolitics        = India-Pakistan relations, India-China, US-India, multilateral diplomacy
wars-conflicts     = Active military conflicts, airstrikes, casualties, war zones globally
world-general      = International news that does not fit geopolitics or wars-conflicts
global-economy     = Global markets, US Fed, oil prices, world trade, sanctions
defence            = Indian or Pakistani military hardware, defence deals, armed forces ops
youtube            = YouTube video uploads only
api-news           = Generic API-sourced news without a better fit"""

_USER_TEMPLATE = """\
Analyze this news article and return ONLY a raw JSON object.

Source: {source}
Suggested category: {category}
Original Title: {title}
Description: {description}
Article Body: {body}

CATEGORY REFERENCE:
{category_guide}

Return this exact JSON:
{{
  "tweaked_title": "<Rewrite the headline in your own words. Identical meaning, different wording. Max 120 chars.>",
  "summary_points": ["<point 1>", "<point 2>", "<point 3>"],
  "why_it_matters": "<Concrete 1-2 sentence implication. Specific about who is affected and how. No vague language.>",
  "confidence": "<confirmed | developing | unverified>",
  "category_refined": "<Pick the single best category from the CATEGORY REFERENCE above based on article content. Ignore the suggested category if a more specific one fits better.>",
  "flag": "<most relevant country flag emoji>",
  "impact_score": <integer 1-10, where 10 is a history-changing event>,
  "x_post": "<Four-line post following the Hook/Insight/Context/Question structure. Zero emojis. Zero m-dashes. Under 280 chars. Source on its own line at the end.>"
}}"""


# ── shared helpers ─────────────────────────────────────────────────────────────

def _build_prompt(title: str, description: str, body: str | None,
                  source: str, category: str) -> str:
    groq_body = (body or "")[:600] or "Not available"
    groq_desc = (description or "")[:300] or "Not available"
    return _USER_TEMPLATE.format(
        source=source,
        category=category,
        title=title,
        description=groq_desc,
        body=groq_body,
        category_guide=_CATEGORY_GUIDE,
    )


def _parse_raw(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    def _fix_newlines(m: re.Match) -> str:
        return m.group(0).replace("\n", "\\n").replace("\r", "")

    raw = re.sub(r'(?<=": ")(.*?)(?="(?:\s*[,}]))', _fix_newlines, raw, flags=re.DOTALL)
    return json.loads(raw)


def _sanitise(result: dict, title: str, category: str) -> dict:
    if result.get("category_refined") not in config.VALID_CATEGORIES:
        result["category_refined"] = category
    result.setdefault("tweaked_title", title)
    result.setdefault("summary_points", ["No summary available."])
    result.setdefault("why_it_matters", "")
    result.setdefault("confidence", "unverified")
    result.setdefault("flag", "🌐")
    result.setdefault("impact_score", 5)
    result.setdefault("x_post", "")

    x = result["x_post"]
    x = re.sub(r"\u2014|\u2013|--", " ", x)
    x = re.sub(r"[^\x00-\x7F\u0900-\u097F\s]", "", x)
    result["x_post"] = x.strip()
    return result


# ── provider calls ─────────────────────────────────────────────────────────────

def _call_groq(user_prompt: str) -> str:
    response = _get_groq().chat.completions.create(
        model=config.GROQ_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.5,
        max_tokens=1500,
    )
    return response.choices[0].message.content


def _call_gemini(user_prompt: str) -> str:
    model = genai.GenerativeModel(
        model_name=config.GEMINI_MODEL,
        system_instruction=_SYSTEM_PROMPT,
    )
    response = model.generate_content(
        user_prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.5,
            max_output_tokens=1500,
        ),
    )
    return response.text


# ── public entry point ─────────────────────────────────────────────────────────

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

    user_prompt = _build_prompt(title, description, body, source, category)

    raw: str | None = None
    provider_used = "none"

    # ── Try Groq first ────────────────────────────────────────────────────
    if config.GROQ_API_KEY:
        try:
            raw = _call_groq(user_prompt)
            provider_used = "groq"
        except GroqRateLimitError as e:
            print(f"[PROCESSOR] Groq rate limit hit, falling back to Gemini. ({e})")
        except Exception as e:
            print(f"[PROCESSOR] Groq error for '{title[:60]}': {type(e).__name__}: {e}")
            fallback["_groq_error"] = f"{type(e).__name__}: {e}"

    # ── Fall back to Gemini if Groq failed or hit rate limit ──────────────
    if raw is None and _get_gemini():
        try:
            raw = _call_gemini(user_prompt)
            provider_used = "gemini"
        except Exception as e:
            print(f"[PROCESSOR] Gemini error for '{title[:60]}': {type(e).__name__}: {e}")
            fallback["_groq_error"] = fallback.get("_groq_error", "") + f" | Gemini: {type(e).__name__}: {e}"

    time.sleep(config.GROQ_DELAY)

    if raw is None:
        return fallback

    try:
        result = _parse_raw(raw)
        result = _sanitise(result, title, category)
        result["_provider"] = provider_used
        return result
    except Exception as e:
        print(f"[PROCESSOR] JSON parse error ({provider_used}) for '{title[:60]}': {e}\nRaw: {raw[:300]}")
        fallback["_groq_error"] = f"JSON parse failed ({provider_used}): {e}"
        return fallback
