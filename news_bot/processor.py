"""
Keyword-based article router. No AI dependency.
Routes articles from catch-all categories (india-general, pak-general, world-general)
to more specific channels based on title + description content.
"""
from __future__ import annotations

# Catch-all categories that benefit from keyword routing.
# Specific categories (india-politics, pak-military, etc.) are kept as-is.
_CATCH_ALLS = {"india-general", "world-general", "pak-general", "api-news"}

# Rules are checked in order — first match wins.
# Keywords matched against lowercase(title + " " + description).
_RULES: list[tuple[list[str], str]] = [

    # ── India: Parliament ─────────────────────────────────────────────────────
    (["lok sabha", "rajya sabha", "parliament", "parliamentary session",
      "member of parliament", " mps ", "no-confidence motion",
      "zero hour", "question hour", "winter session", "budget session",
      "monsoon session", "joint session", "protem speaker"], "india-parliament"),

    # ── India: Elections ──────────────────────────────────────────────────────
    (["election commission", "evm ", "vvpat", "bypoll", "by-poll", "by poll",
      "lok sabha election", "assembly election", "state election",
      "election result", "polling day", "voter turnout", "seat tally",
      "exit poll", "vote counting", "model code of conduct"], "india-elections"),

    # ── India: States ─────────────────────────────────────────────────────────
    (["chief minister", "state government", "governor's rule",
      "president's rule", "vidhan sabha", "state assembly", "state cabinet",
      "state budget", "state police", "municipal corporation",
      "panchayat"], "india-states"),

    # ── India: Markets ────────────────────────────────────────────────────────
    (["sensex", "nifty", "bse ", "nse ", " ipo ", "stock market",
      "mutual fund", " sebi ", " fii ", "share price", "equity market",
      "d-street", "dalal street", "market cap", "stock exchange",
      "trade deficit india", "foreign portfolio"], "india-markets"),

    # ── India: Economy ────────────────────────────────────────────────────────
    (["rbi ", "repo rate", " gdp ", "india inflation", "fiscal deficit",
      "finance ministry", "niti aayog", "economic survey",
      "india's economy", "indian economy", "union budget",
      "tax collection", "gst collection"], "india-economy"),

    # ── India: Govt Policy ────────────────────────────────────────────────────
    (["cabinet approves", "cabinet clears", "ordinance", "central scheme",
      "pm launches", "flagship scheme", "pli scheme", "make in india",
      "new policy", "government directive", "ministry announces",
      "regulatory framework", "national mission"], "india-govt-policy"),

    # ── India: Politics ───────────────────────────────────────────────────────
    (["bjp", "indian national congress", " inc ", "aam aadmi party",
      "trinamool", " tmc ", "samajwadi party", "shiv sena", " ncp ",
      " dmk ", "narendra modi", "rahul gandhi", "amit shah",
      "arvind kejriwal", "mamata banerjee", "yogi adityanath",
      "opposition alleges", "ruling party"], "india-politics"),

    # ── India: Hindu-Muslim ───────────────────────────────────────────────────
    (["mosque", "masjid", "temple dispute", "mandir", "communal tension",
      "communal violence", "religious conversion", "waqf board",
      "love jihad", "hindutva", "cow vigilante", "gyanvapi",
      "mathura mosque", "ayodhya", "anti-hindu", "anti-muslim",
      "minority community"], "hindu-muslim"),

    # ── India: Scandals ───────────────────────────────────────────────────────
    (["cbi raid", "ed raid", "enforcement directorate", "money laundering",
      "hawala", "corruption case", "ponzi scheme", "bribery",
      "sex scandal", "posh complaint", "arrested for fraud",
      "financial scam", "embezzlement"], "scandals-outrages"),

    # ── Pakistan: Military ────────────────────────────────────────────────────
    (["pakistan army", "ispr", " coas ", "isi ", "military court",
      "civil-military", "pakistan air force", "pakistan navy",
      "general asim munir", "pak army", "inter-services",
      "operation azm-e-istehkam"], "pak-military"),

    # ── Pakistan: Economy ─────────────────────────────────────────────────────
    (["pakistan imf", "pakistan rupee", "pakistan economy",
      "pakistan inflation", "cpec", "pakistan gdp", "pakistan debt",
      "state bank of pakistan", "pakistan trade deficit",
      "pakistan forex", "pakistan budget"], "pak-economy"),

    # ── Pakistan: Government ─────────────────────────────────────────────────
    (["imran khan", "shehbaz sharif", "bilawal bhutto", "pml-n",
      " ppp ", "pakistan cabinet", "national assembly pakistan",
      "pakistan parliament", "pakistan prime minister",
      "asif zardari", "pakistan government", "pakistan minister",
      "pakistan senator"], "pak-government"),

    # ── Wars & Conflicts ──────────────────────────────────────────────────────
    (["airstrike", "missile strike", "troops advance", "military offensive",
      "killed in fighting", "war casualties", "ceasefire violated",
      "drone attack", "ground offensive", "war in ukraine", "gaza strip",
      "sudan war", "myanmar conflict", "hamas", "hezbollah",
      "russian forces", "ukrainian forces", "israel strikes"], "wars-conflicts"),

    # ── Geopolitics ───────────────────────────────────────────────────────────
    (["india-china", "india-pakistan relations", "bilateral talks",
      "foreign minister meets", "united nations", " nato ", "g20 summit",
      "g7 summit", "quad summit", "brics", "sco summit",
      "indo-pacific", "line of actual control", "loc tension",
      "diplomatic ties", "sanctions on"], "geopolitics"),

    # ── Global Economy ────────────────────────────────────────────────────────
    (["federal reserve", "fed rate", "oil prices", "crude oil price",
      "global trade", "world bank loan", "imf programme",
      "global inflation", "dollar index", "us economy recession",
      "european central bank", "china economy"], "global-economy"),

    # ── Defence ───────────────────────────────────────────────────────────────
    (["defence deal", "rafale", "tejas ", "brahmos", "aircraft carrier",
      "indian army exercise", "indian navy exercise", "indian air force",
      " drdo ", "defence ministry", "defence budget",
      "fighter jet", "submarine deal", "weapon system"], "defence"),
]


def route_article(title: str, description: str, default_category: str) -> str:
    """
    Returns the best-fit category for this article.
    Only overrides the default if it is a catch-all category.
    Specific categories (india-politics, pak-military, etc.) are kept as-is.
    """
    if default_category not in _CATCH_ALLS:
        return default_category

    text = (title + " " + (description or "")).lower()

    for keywords, target in _RULES:
        if any(kw in text for kw in keywords):
            return target

    return default_category
