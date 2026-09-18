from dealr.config.dealr_config import get_dealr_config
from dealr.db.inventory_repo import save_inventory, update_inventory_db
from f1ndr.vin.decode import decode_vin
from f1ndr.intelligence.market import compute_market_value
from listr.core.core import push_listing, update_listing
from trinn.core.core import schedule_sync
import asyncio


def ingest_inventory(data: dict) -> dict:
    config = get_dealr_config()

    if config["enable_vin_decode"] and "vin" in data:
        decoded = decode_vin(data["vin"])
        data.update(decoded)

    if config["enable_market_value"]:
        data["market_value"] = compute_market_value(data)

    save_inventory(data)
    return data


def sync_inventory(data: dict) -> dict:
    config = get_dealr_config()

    for platform in config["default_platforms"]:
        update_listing(platform, data)

    # Run async schedule_sync in event loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    loop.run_until_complete(schedule_sync(data, config["sync_interval_hours"]))
    update_inventory_db(data)
    return data
