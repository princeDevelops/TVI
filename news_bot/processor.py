"""
Keyword-based article router. No AI dependency.

Routing applies to every article (except youtube and google-alerts).
Rules are checked in order — first match wins.
BRICS keywords take universal highest priority.
"""
from __future__ import annotations

# These categories are never re-routed — they stay as posted.
_ROUTING_EXEMPT = {"youtube", "google-alerts"}

# ── BRICS: universal override ─────────────────────────────────────────────────
# Fires before all other rules regardless of source feed.
_BRICS_KEYWORDS = [
    "brics", "new development bank", "ndb bank",
    "de-dollarisation", "de-dollarization", "dedollarization",
    "brics currency", "brics expansion", "brics summit", "brics nation",
    "brics member", "brics countries", "brics bloc",
    "sco summit", "shanghai cooperation organisation",
    "shanghai cooperation organization",
]

# ── WATCHLIST: triggers a breaking-alert post in addition to normal routing ───
_WATCHLIST_KEYWORDS = [
    "adani", "ambani",
    "rahul gandhi arrested", "modi arrested", "pm arrested",
    "nuclear war", "nuclear strike", "nuclear attack",
    "india coup", "military coup",
    "stock market crash", "market crash india", "sensex crash",
    "rupee crash", "rupee collapses", "rupee hits all-time low",
    "bomb blast india", "bomb blast in india",
    "terror attack india", "terror attack in india",
    "election results india", "election result india",
    "major earthquake", "massive earthquake",
    "supreme court verdict india",
]

# ── Main routing rules (order matters — first match wins) ─────────────────────
_RULES: list[tuple[list[str], str]] = [

    # ── Pakistan: Military (before pak-general) ───────────────────────────────
    (["pakistan army", "pak army", "ispr", "coas pakistan",
      "isi pakistan", "asim munir", "pakistan air force paf",
      "pakistan navy", "inter-services intelligence",
      "operation azm-e-istehkam", "pakistan military court",
      "pakistan military operation", "civil-military pakistan",
      "ttp ", "tehrik-i-taliban", "lashkar", "jaish",
      "pakistan militant", "pakistan terror group"], "pak-military"),

    # ── Pakistan: Economy (before pak-general) ────────────────────────────────
    (["pakistan imf", "pakistan rupee", "pakistan economy",
      "pakistan inflation", "cpec", "pakistan gdp", "pakistan debt",
      "pakistan default", "state bank of pakistan", "pakistan forex",
      "pakistan budget", "pakistan trade deficit", "pakistan loan",
      "pakistan financial crisis", "pakistan growth"], "pak-economy"),

    # ── Pakistan: Government (before pak-general) ─────────────────────────────
    (["imran khan", "pti ", "tehreek-e-insaf",
      "shehbaz sharif", "pmln", "pml-n", "nawaz sharif",
      "bilawal bhutto", "ppp ", "asif zardari", "maulana fazlur",
      "pakistan parliament", "national assembly pakistan",
      "pakistan prime minister", "pakistan cabinet",
      "pakistan politics", "pakistan election", "pakistan political",
      "pakistan government", "pakistan minister", "pakistan senator",
      "pakistan supreme court", "pakistan judiciary",
      "pakistan court ruling"], "pak-government"),

    # ── India: Parliament ─────────────────────────────────────────────────────
    (["lok sabha", "rajya sabha", "india parliament",
      "parliamentary session", "parliament session",
      "member of parliament", "no-confidence motion",
      "zero hour parliament", "question hour",
      "winter session", "budget session", "monsoon session",
      "joint session", "protem speaker", "speaker lok sabha"], "india-parliament"),

    # ── India: Elections ──────────────────────────────────────────────────────
    (["election commission", "evm", "vvpat", "bypoll", "by-poll",
      "lok sabha election", "assembly election", "state election",
      "india election", "election result india", "polling day",
      "voter turnout", "seat tally", "exit poll",
      "vote counting india", "model code of conduct",
      "election schedule", "india vote", "india campaign",
      "booth capturing", "polling booth india"], "india-elections"),

    # ── India: States ─────────────────────────────────────────────────────────
    (["chief minister", "india chief minister", "india cm",
      "state government india", "governor's rule", "president's rule",
      "vidhan sabha", "state assembly india", "state cabinet india",
      "state budget india", "municipal corporation india",
      "panchayat india", "district collector",
      "uttar pradesh", "maharashtra government", "rajasthan government",
      "madhya pradesh government", "west bengal government",
      "tamil nadu government", "karnataka government",
      "telangana government", "andhra pradesh government",
      "bihar government", "gujarat government", "punjab government",
      "haryana government", "kerala government"], "india-states"),

    # ── India: Markets ────────────────────────────────────────────────────────
    (["sensex", "nifty", "bse ", "nse ", " ipo india", "india market",
      "india stock market", "mutual fund india", "sebi ",
      "fii ", "share price india", "equity market india",
      "dalal street", "d-street", "market cap india",
      "india forex", "rupee vs dollar", "india rupee",
      "fpi india", "india ipo", "smallcap india", "midcap india",
      "india market rally", "india market crash",
      "foreign portfolio investor"], "india-markets"),

    # ── India: Economy ────────────────────────────────────────────────────────
    (["india economy", "indian economy", "india gdp", "india growth",
      "rbi ", "repo rate", "reserve bank of india",
      "india interest rate", "india inflation", "india recession",
      "india fiscal", "india budget", "india tax", "india trade",
      "india export", "india import", "india tariff", "india fdi",
      "india investment", "india unemployment", "india jobs",
      "india layoffs", "india startup", "india unicorn",
      "india oil price", "india fuel", "india manufacturing",
      "india infrastructure", "india agriculture",
      "india finance ministry", "niti aayog",
      "economic survey india", "india gst", "india upi economy"], "india-economy"),

    # ── India: Govt & Policy ──────────────────────────────────────────────────
    (["india new law", "india legislation", "india bill passed",
      "india government policy", "india regulation",
      "india ministry announcement", "india cabinet decision",
      "india executive order", "cabinet approves", "cabinet clears",
      "ordinance india", "central scheme", "pm launches",
      "flagship scheme", "pli scheme", "make in india",
      "india climate policy", "india environment policy",
      "india healthcare policy", "india education policy",
      "india tax reform", "india welfare scheme", "india yojana",
      "digital india", "india data protection", "india aadhaar",
      "india upi policy", "india supreme court ruling",
      "india high court ruling", "india regulatory",
      "national mission india", "india government initiative",
      "pm modi announces", "pm modi launches",
      "india smart city", "swachh bharat", "pmay",
      "ayushman bharat", "jan dhan"], "india-govt-policy"),

    # ── India: Politics ───────────────────────────────────────────────────────
    (["bjp", "indian national congress", "congress party",
      "aam aadmi party", "aap india", "trinamool", "tmc india",
      "samajwadi party", "bsp india", "shiv sena",
      "narendra modi", "rahul gandhi", "amit shah",
      "arvind kejriwal", "mamata banerjee", "yogi adityanath",
      "smriti irani", "rajnath singh", "j.p. nadda",
      "mallikarjun kharge", "priyanka gandhi",
      "india coalition", "india political", "india opposition",
      "nda ", "india alliance", "indi alliance",
      "india political crisis", "india no confidence",
      "india mp ", "india mla ", "india minister arrested",
      "india politician arrested", "ruling party india",
      "opposition india", "india pm ", "india president"], "india-politics"),

    # ── Hindu-Muslim ──────────────────────────────────────────────────────────
    (["communal", "lynching", "waqf", "halal", "hijab",
      "masjid", "mandir", "azaan", "namaz",
      "mob attack religious", "religious tension", "religious conflict",
      "temple dispute", "mosque dispute", "communal violence",
      "communal riot", "communal clash", "hindu muslim clash",
      "religious violence", "mob lynching", "cow vigilante",
      "bajrang dal", "vhp attack", "love jihad",
      "forced conversion", "conversion racket", "ghar wapsi",
      "religious conversion india", "anti-conversion law",
      "temple demolition", "mosque demolition",
      "waqf board", "waqf controversy", "places of worship act",
      "hindu killed", "muslim killed", "priest attacked",
      "maulana arrested", "imam arrested", "hindu monk killed",
      "hate speech india", "islamophobia india", "anti-hindu",
      "minority attack india", "ucc india", "uniform civil code",
      "triple talaq", "population jihad", "land jihad",
      "pfi banned", "popular front india", "hindu mahasabha",
      "economic boycott hindu", "halal controversy",
      "islamic banking india", "demographic jihad",
      "urban jihad", "land grab india", "hijab ban india",
      "loudspeaker mosque", "hindutva"], "hindu-muslim"),

    # ── Scandals & Outrages ───────────────────────────────────────────────────
    (["india scandal", "india corruption", "india fraud", "india scam",
      "india arrested", "india politician arrested",
      "india minister arrested", "india controversy",
      "india resign", "india sacked", "india cover-up",
      "india leaked", "india exposed", "india outrage",
      "india backlash", "india protest", "india rape",
      "india murder", "india crime",
      "cbi raid", "cbi india", "ed raid", "enforcement directorate",
      "money laundering india", "india bribery", "india hawala",
      "india whistleblower", "india probe", "india inquiry",
      "india riot", "india violence", "india attack",
      "bollywood controversy", "india celebrity scandal",
      "income tax raid india", "benami property",
      "disproportionate assets india", "ponzi india",
      "financial scam india", "drug bust india",
      "drug trafficking india", "crime india"], "scandals-outrages"),

    # ── Wars & Conflicts ──────────────────────────────────────────────────────
    (["airstrike", "missile strike", "troops advance",
      "military offensive", "killed in fighting", "war casualties",
      "ceasefire violated", "drone attack", "ground offensive",
      "war in ukraine", "gaza strip", "sudan war",
      "myanmar conflict", "hamas", "hezbollah",
      "russian forces", "ukrainian forces", "israel strikes",
      "bombing campaign", "shelling", "artillery fire",
      "frontline war", "war crime", "siege of",
      "occupied territory", "military escalation",
      "iran nuclear strike", "north korea missile",
      "taiwan strait conflict", "south china sea conflict",
      "nato vs russia", "pakistan terror attack",
      "india pakistan war", "terror attack",
      "bomb blast", "suicide bombing"], "wars-conflicts"),

    # ── Geopolitics ───────────────────────────────────────────────────────────
    (["india pakistan", "india china", "india border",
      "line of control", "loc ", "lac ", "kashmir conflict",
      "india foreign policy", "india us relations",
      "india russia", "india israel", "india iran",
      "india sri lanka", "india nepal", "india bangladesh",
      "india maldives", "india myanmar", "india bhutan",
      "quad india", "india military deployed",
      "india ceasefire", "india sanctions", "india un",
      "india g20", "india sco", "india brics",
      "doklam", "arunachal pradesh china",
      "india missile test", "india nuclear",
      "bilateral talks", "foreign minister india",
      "united nations india", "nato ", "g20 summit",
      "g7 summit", "quad summit", "indo-pacific",
      "diplomatic ties india", "india ambassador",
      "ministry of external affairs", "mea india",
      "india-us", "india-russia", "india-japan",
      "india-australia", "india foreign"], "geopolitics"),

    # ── Global Economy ────────────────────────────────────────────────────────
    (["federal reserve", "fed rate", "oil prices", "crude oil price",
      "global trade", "world bank loan", "imf programme",
      "global inflation", "dollar index", "us economy recession",
      "european central bank", "china economy", "global gdp",
      "wto ", "opec ", "brent crude", "gold price",
      "global supply chain", "trade war", "us tariff",
      "china tariff", "us economy", "euro zone",
      "global recession", "world economy",
      "commodity market global"], "global-economy"),

    # ── Defence ───────────────────────────────────────────────────────────────
    (["defence deal india", "rafale", "tejas", "brahmos",
      "aircraft carrier india", "indian army exercise",
      "indian navy exercise", "indian air force exercise",
      "drdo", "defence ministry india", "defence budget india",
      "fighter jet india", "submarine deal india",
      "weapon system india", "india military exercise",
      "indian army", "indian navy", "iaf india",
      "india defence", "indigenisation defence",
      "atmanirbhar defence", "defence corridor india",
      "defence expo india", "defence acquisition india",
      "surgical strike", "army chief india",
      "navy chief india", "air chief india",
      "border security india", "bsf india", "crpf india"], "defence"),

    # ── Pakistan General (broad Pakistan catch-all) ───────────────────────────
    (["pakistan", "pakistani", "karachi", "lahore", "islamabad",
      "rawalpindi", "peshawar", "quetta",
      "mahira khan", "fawad khan", "pakistan celebrity",
      "pakistan actor", "geo news", "dawn news", "ary news",
      "pakistan viral", "pakistan trending",
      "pakistan news", "pakistan crisis"], "pak-general"),

    # ── India General (broad India catch-all — must come last) ────────────────
    (["india", "indian", "bharat", "hindustan",
      "delhi", "mumbai", "bangalore", "bengaluru",
      "chennai", "hyderabad", "kolkata", "pune",
      "ahmedabad", "jaipur", "isro", "drdo india",
      "supreme court of india"], "india-general"),
]


def route_article(title: str, description: str, default_category: str) -> str:
    """
    Returns the best-fit category for an article.

    - YouTube and Google Alerts are never re-routed.
    - BRICS keywords override every other rule.
    - All remaining rules apply to every article; default_category
      is only used if nothing matches.
    """
    if default_category in _ROUTING_EXEMPT:
        return default_category

    text = (title + " " + (description or "")).lower()

    # BRICS: universal highest priority
    if any(kw in text for kw in _BRICS_KEYWORDS):
        return "brics"

    for keywords, target in _RULES:
        if any(kw in text for kw in keywords):
            return target

    return default_category


def is_watchlist(title: str, description: str) -> bool:
    """Returns True if the article matches high-priority watchlist keywords."""
    text = (title + " " + (description or "")).lower()
    return any(kw in text for kw in _WATCHLIST_KEYWORDS)
