from __future__ import annotations

import sys
import time
import traceback
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

import config
import database
import digest
import fetcher
import poster
import processor
import scraper

_MORNING_UTC = (1, 30)
_EVENING_UTC = (14, 30)
_DIGEST_WINDOW = 20


def _is_digest_time(hour: int, minute: int) -> bool:
    now = datetime.now(timezone.utc)
    return now.hour == hour and abs(now.minute - minute) <= _DIGEST_WINDOW


def _enrich(article: dict) -> None:
    """Scrape image + body, then keyword-route to the best category."""
    if article.get("type") == "youtube":
        article["image_url"] = article.get("thumbnail_url")
        article["body"] = None
        return

    try:
        scraped = scraper.get_article_data(article["url"])
        article["image_url"] = scraped.get("image_url")
        article["body"] = scraped.get("body")
    except Exception:
        article["image_url"] = None
        article["body"] = None

    article["category"] = processor.route_article(
        title=article["title"],
        description=article.get("description", ""),
        default_category=article["category"],
    )


def main() -> None:
    run_start = datetime.now(timezone.utc)
    print(f"[MAIN] Starting at {run_start.isoformat()}")

    database.init_db()
    database.purge_old_stories()

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

    print("[MAIN] Fetching feeds...")
    all_articles, feed_health = fetcher.fetch_all_feeds()

    for fn_name, fn in [
        ("NewsAPI", fetcher.fetch_newsapi),
        ("GNews", fetcher.fetch_gnews),
        ("Currents", fetcher.fetch_currents),
    ]:
        try:
            all_articles.extend(fn())
        except Exception as e:
            poster.post_error(f"{fn_name} fetch failed: {e}")

    new_articles = [a for a in all_articles if not database.is_seen(a["url"])]
    print(f"[MAIN] {len(new_articles)} new / {len(all_articles)} total")

    new_articles.sort(
        key=lambda a: a.get("published") or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    new_articles = new_articles[:config.MAX_ARTICLES_PER_RUN]

    total_posted = 0
    for idx, article in enumerate(new_articles, 1):
        try:
            print(f"[MAIN] [{idx}/{len(new_articles)}] {article['source']} — {article['title'][:70]}")
            _enrich(article)
            poster.post_article(article)
            if processor.is_watchlist(article["title"], article.get("description", "")):
                poster.post_breaking_alert(article)
            database.mark_seen(article)
            database.save_daily_story(article)
            total_posted += 1
            time.sleep(config.ARTICLE_DELAY)
        except Exception as e:
            msg = f"Error: {e}\nTitle: {article.get('title','')[:100]}"
            print(f"[MAIN] {msg}")
            poster.post_error(msg)

    try:
        poster.post_feed_health(feed_health, total_posted)
    except Exception as e:
        print(f"[MAIN] Feed health failed: {e}")

    elapsed = (datetime.now(timezone.utc) - run_start).seconds
    poster.post_log(
        f"Run complete — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} | "
        f"Posted: {total_posted} | Feeds: {len(feed_health)} | Elapsed: {elapsed}s"
    )
    print(f"[MAIN] Done. {total_posted} articles in {elapsed}s.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        tb = traceback.format_exc()
        print(f"[MAIN] FATAL:\n{tb}")
        try:
            poster.post_error(f"FATAL ERROR:\n```{tb[:1800]}```")
        except Exception:
            pass
        sys.exit(1)
