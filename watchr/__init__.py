from .config.config import get_watchr_config
from .core.core import (
    create_alert,
    create_subscription,
    delete_alert,
    delete_subscription,
    get_alert,
    get_subscription,
    list_alerts,
    list_subscriptions,
    register_listing_alerts,
    scan_alerts,
)


async def run(action: str, data: dict) -> dict:
    if action == "create_alert":
        return await create_alert(data)
    if action == "create_subscription":
        return await create_subscription(data)
    if action == "register":
        return await register_listing_alerts(data)
    if action == "list_alerts":
        return await list_alerts(**data)
    if action == "list_subscriptions":
        return await list_subscriptions(**data)
    if action == "delete_alert":
        return await delete_alert(data["alert_id"])
    if action == "delete_subscription":
        return await delete_subscription(data["subscription_id"])
    if action == "scan":
        return {"alerts": await scan_alerts(data.get("limit", 100))}
    raise ValueError(f"Invalid watchr action: {action}")


__all__ = ["get_watchr_config", "run"]
