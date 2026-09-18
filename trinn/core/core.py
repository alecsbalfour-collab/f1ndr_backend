from trinn.config.config import get_trinn_config
from trinn.db.trinn_repo import save_task, update_task_status
from trinn.utils.scheduler import schedule_interval
from scrapers.module import SCRAPERS
from f1ndr.vin.decode import decode_vin
from watchr.core.core import scan_alerts
from listr.core.core import update_listing


def run_task(data: dict) -> dict:
    config = get_trinn_config()
    task_type = data.get("task")

    if task_type == "scrape" and config["enable_scraper_tasks"]:
        platform = data.get("platform")
        scraper_func = SCRAPERS.get(platform)
        if scraper_func:
            return scraper_func(platform)
        else:
            raise ValueError(f"Unsupported scraper platform: {platform}")

    if task_type == "vin" and config["enable_vin_tasks"]:
        return decode_vin(data.get("vin"))

    if task_type == "watchr" and config["enable_watchr_tasks"]:
        return scan_alerts()

    if task_type == "sync" and config["enable_listing_sync"]:
        return update_listing(data.get("platform"), data.get("listing"))

    raise ValueError("Invalid or disabled trinn task")


def schedule_task(data: dict) -> dict:
    config = get_trinn_config()
    interval = data.get("interval", config["default_interval_hours"])

    schedule_interval(data, interval)
    save_task(data)

    return {"scheduled": True, "interval": interval}
