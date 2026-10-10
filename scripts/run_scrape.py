"""Standalone scrape runner for environments outside the API process.

Chromium does not fit in the 512MB container the API runs on, so scraping runs
here instead (GitHub Actions, a worker box, locally). Opens the shared Mongo
connection, runs the requested platform(s) through the normal pipeline — results
upsert into `f1ndr_listings` and feed watchr alert matching — then retries any
alert emails that failed earlier, and exits.

Usage:
    python scripts/run_scrape.py --platform kijiji --query civic
    python scripts/run_scrape.py --platform all

Exits 0 when at least one platform succeeded, 1 when all failed, 2 when MongoDB
is unreachable (nothing would persist anyway).
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.config.settings_config import get_settings
from db.connection_db import close_db_connection, connect_to_db, get_database
from scrapers.module import SCRAPER_CLASSES, run_scraper
from watchr.core.core import retry_pending_notifications


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--platform", required=True,
                        choices=sorted(SCRAPER_CLASSES) + ["all"])
    parser.add_argument("--query", default=None)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")

    await connect_to_db()
    if get_database() is None:
        print("MongoDB unreachable; results would not persist. Aborting.", file=sys.stderr)
        return 2
    if not get_settings().SMTP_HOST:
        print("SMTP_HOST not set: watchr matches will be recorded but no alert emails sent.",
              file=sys.stderr)

    try:
        platforms = list(SCRAPER_CLASSES) if args.platform == "all" else [args.platform]
        failed = 0
        for name in platforms:
            result = await run_scraper(name, args.query or None)
            ok = result.get("success", False)
            failed += 0 if ok else 1
            print(f"{name}: success={ok} count={result.get('count', 0)} "
                  f"error={result.get('error')}")
        try:
            print(f"watchr notification retry: {await retry_pending_notifications()}")
        except Exception:
            logging.exception("watchr notification retry failed")
        return 1 if failed == len(platforms) else 0
    finally:
        await close_db_connection()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
