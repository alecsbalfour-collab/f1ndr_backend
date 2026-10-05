"""Standalone scrape runner for environments outside the API process.

Chromium does not fit in the 512MB container the API runs on, so scraping runs
here instead (GitHub Actions, a worker box, locally). Opens the shared Mongo
connection, runs the requested platform(s) through the normal pipeline — results
upsert into `f1ndr_listings` and feed watchr alert matching — then exits.

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

from db.connection_db import close_db_connection, connect_to_db, get_database
from scrapers.module import SCRAPER_CLASSES, run_scraper


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

    try:
        platforms = list(SCRAPER_CLASSES) if args.platform == "all" else [args.platform]
        failed = 0
        for name in platforms:
            result = await run_scraper(name, args.query or None)
            ok = result.get("success", False)
            failed += 0 if ok else 1
            print(f"{name}: success={ok} count={result.get('count', 0)} "
                  f"error={result.get('error')}")
        return 1 if failed == len(platforms) else 0
    finally:
        await close_db_connection()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
