from sellr.config.config import get_listings_config
from f1ndr.vin.decode import decode_vin
from f1ndr.intelligence.market import compute_market_value
from listr.core.core import push_listing
from watchr.core.core import register_listing_alerts
from trinn.core.core import schedule_sync


def validate_listing(data: dict, config: dict) -> dict:
    title = data.get("title", "")
    price = data.get("price", 0)

    if len(title) > config["max_title_length"]:
        title = title[:config["max_title_length"]]

    if price < config["min_price"]:
        raise ValueError("Price below minimum allowed")

    return {**data, "title": title, "price": price}


def autofill_from_vin(data: dict, config: dict) -> dict:
    if not config["enable_vin_autofill"]:
        return data

    vin = data.get("vin")
    if not vin:
        return data

    decoded = decode_vin(vin)
    return {**data, **decoded}


def apply_auto_pricing(data: dict, config: dict) -> dict:
    if not config["auto_price"]:
        return data

    market_value = compute_market_value(data)
    if not market_value:
        return data
    floor = market_value * config["price_floor_percent"]
    ceiling = market_value * config["price_ceiling_percent"]

    price = max(floor, min(data["price"], ceiling))
    return {**data, "price": price}


def push_to_marketplaces(listing: dict, config: dict):
    if not config["allow_multi_platform"]:
        return

    for platform in config["default_platforms"]:
        push_listing(platform, listing)


def setup_alerts(listing: dict, config: dict):
    if config["enable_watchr_alerts"]:
        register_listing_alerts(listing)


async def schedule_listing_sync(listing: dict, config: dict):
    await schedule_sync(listing, config["auto_sync_interval_hours"])


async def create_listing(data: dict) -> dict:
    config = get_listings_config()

    listing = validate_listing(data, config)
    listing = autofill_from_vin(listing, config)
    listing = apply_auto_pricing(listing, config)
    push_to_marketplaces(listing, config)
    setup_alerts(listing, config)
    await schedule_listing_sync(listing, config)

    return listing
