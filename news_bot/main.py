from __future__ import annotations

import sys
import time
import traceback
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

import config  # noqa: E402 — after load_dotenv
import database
import digest
import fetcher
import poster
import processor
import scraper

# UTC times for digest windows
_MORNING_UTC = (1, 30)   # 07:00 IST
_EVENING_UTC = (14, 30)  # 20:00 IST
_DIGEST_WINDOW = 14      # ±14 minutes tolerance


def _is_digest_time(target_hour: int, target_minute: int) -> bool:
    now = datetime.now(timezone.utc)
    if now.hour != target_hour:
        return False
    return abs(now.minute - target_minute) <= _DIGEST_WINDOW


def _process_one(article: dict) -> dict:
    """Scrape + AI-process a single article. Returns ai_result dict."""
    if article.get("type") == "youtube":
        article["image_url"] = article.get("thumbnail_url")
        article["body"] = None
        return {
            "tweaked_title": article["title"],
            "summary_points": [],
            "why_it_matters": "",
            "confidence": "confirmed",
            "category_refined": "youtube",
            "flag": "▶️",
        }

    scraped = scraper.get_article_data(article["url"])
    article["image_url"] = scraped.get("image_url")
    article["body"] = scraped.get("body")

    return processor.process_article(
        title=article["title"],
        description=article.get("description", ""),
        body=article.get("body"),
        source=article["source"],
        category=article["category"],
    )


def _check_groq_key() -> bool:
    key = config.GROQ_API_KEY
    if not key:
        msg = "GROQ_API_KEY is missing or empty. Check GitHub Secrets."
        print(f"[MAIN] ERROR: {msg}")
        poster.post_error(msg)
        return False
    if not key.startswith("gsk_"):
        msg = f"GROQ_API_KEY looks malformed (expected gsk_..., got {key[:6]}...). Re-copy from console.groq.com."
        print(f"[MAIN] ERROR: {msg}")
        poster.post_error(msg)
        return False
    print(f"[MAIN] GROQ_API_KEY present ({key[:8]}...).")
    return True


def main() -> None:
    run_start = datetime.now(timezone.utc)
    print(f"[MAIN] News bot starting at {run_start.isoformat()}")

    database.init_db()
    database.purge_old_stories()

    if not _check_groq_key():
        poster.post_log("Run aborted: Groq key invalid. No articles processed.")
        return

    # ── digest check ──────────────────────────────────────────────────────
    if _is_digest_time(*_MORNING_UTC):
        try:
            digest.morning_digest()
        except Exception as e:
            poster.post_error(f"Morning digest failed: {e}")

    if _is_digest_time(*_EVENING_UTC):
        try:
            digest.evening_digest()
        except Exception as e:
            poster.post_error(f"Evening digest failed: {e}")

    # ── fetch all RSS / YouTube feeds ─────────────────────────────────────
    print("[MAIN] Fetching RSS and YouTube feeds...")
    all_articles, feed_health = fetcher.fetch_all_feeds()

    # ── fetch API sources (optional — skip gracefully if no key) ──────────
    for fn_name, fn in [
        ("NewsAPI", fetcher.fetch_newsapi),
        ("GNews", fetcher.fetch_gnews),
        ("Currents", fetcher.fetch_currents),
    ]:
        try:
            api_arts = fn()
            all_articles.extend(api_arts)
        except Exception as e:
            poster.post_error(f"{fn_name} fetch failed: {e}")

    # ── filter to unseen articles ─────────────────────────────────────────
    new_articles = [a for a in all_articles if not database.is_seen(a["url"])]
    print(f"[MAIN] {len(new_articles)} new / {len(all_articles)} total articles")

    # Sort newest-first; cap at limit
    new_articles.sort(
        key=lambda a: a.get("published") or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    new_articles = new_articles[: config.MAX_ARTICLES_PER_RUN]

    # ── process and post each article ─────────────────────────────────────
    total_posted = 0

    for idx, article in enumerate(new_articles, start=1):
        try:
            print(
                f"[MAIN] [{idx}/{len(new_articles)}] {article['source']} — "
                f"{article['title'][:70]}"
            )
            ai_result = _process_one(article)
            if ai_result.get("_groq_error"):
                poster.post_error(
                    f"Groq failed for: {article['title'][:80]}\n"
                    f"Error: {ai_result['_groq_error']}"
                )
            poster.post_article(article, ai_result)
            database.mark_seen(article)
            database.save_daily_story(article, ai_result)
            total_posted += 1
            time.sleep(config.ARTICLE_DELAY)

        except Exception as e:
            msg = (
                f"Article processing error: {e}\n"
                f"Title: {article.get('title', 'unknown')[:100]}\n"
                f"URL: {article.get('url', 'unknown')}"
            )
            print(f"[MAIN] {msg}")
            poster.post_error(msg)

    # ── post health and run summary ───────────────────────────────────────
    try:
        poster.post_feed_health(feed_health, total_posted)
    except Exception as e:
        print(f"[MAIN] Feed health report failed: {e}")

    elapsed = (datetime.now(timezone.utc) - run_start).seconds
    try:
        poster.post_log(
            f"✅ Run complete — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} | "
            f"Posted: {total_posted} | "
            f"Feeds: {len(feed_health)} | "
            f"Elapsed: {elapsed}s"
        )
    except Exception as e:
        print(f"[MAIN] Log posting failed: {e}")

    print(f"[MAIN] Done. Posted {total_posted} articles in {elapsed}s.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        tb = traceback.format_exc()
        print(f"[MAIN] FATAL:\n{tb}")
        try:
            poster.post_error(f"🚨 FATAL RUN ERROR:\n```{tb[:1800]}```")
        except Exception:
            pass
        sys.exit(1)
