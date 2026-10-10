from dealr.config.dealr_config import get_dealr_config
from dealr.db.inventory_repo import get_inventory, save_inventory, update_inventory_db
from f1ndr.vin.decode import decode_vin
from f1ndr.intelligence.market import compute_market_value
from listr.core.core import update_listing
from trinn.core.core import schedule_sync


async def ingest_inventory(data: dict) -> dict:
    config = get_dealr_config()

    if config["enable_vin_decode"] and "vin" in data:
        decoded = decode_vin(data["vin"])
        data.update(decoded)

    if config["enable_market_value"]:
        data["market_value"] = compute_market_value(data)

    await save_inventory(data)
    return data


async def sync_inventory(data: dict) -> dict:
    config = get_dealr_config()

    for platform in config["default_platforms"]:
        await update_listing(platform, data)

    await update_inventory_db(data)
    # Updates are partial: schedule from the merged document so an omitted
    # platform isn't read as "removed" (which would cancel the sync task).
    await schedule_sync(await get_inventory(data["id"]) or data, config["sync_interval_hours"])
    return data
