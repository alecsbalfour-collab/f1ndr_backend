"""Search links to platforms f1ndr doesn't collect data from.

Facebook Marketplace forbids automated collection (Facebook Terms 3.2.3 and
Meta's Automated Data Collection Terms, logged in or not), so f1ndr never scrapes
it. Instead the client shows a button that opens the user's search on Marketplace
in their own browser or app.
"""

from typing import Dict, List, Optional
from urllib.parse import urlencode

FACEBOOK_MARKETPLACE = "https://www.facebook.com/marketplace"

# Marketplace category pages, used when there's no free-text query to search for.
_FB_CATEGORY_PATHS = {"vehicles": "vehicles", "real_estate": "propertyforsale"}


def _city_slug(region: Optional[str]) -> str:
    """f1ndr region -> Marketplace city path segment ("Calgary" -> "calgary")."""
    return "".join(ch for ch in (region or "").lower() if ch.isalnum())


def facebook_marketplace_url(
    query: Optional[str] = None,
    region: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> str:
    """Marketplace URL for a search. Without a region, Facebook uses the user's own location."""
    city = _city_slug(region)
    base = f"{FACEBOOK_MARKETPLACE}/{city}" if city else FACEBOOK_MARKETPLACE
    params: Dict[str, object] = {}
    if min_price is not None:
        params["minPrice"] = int(min_price)
    if max_price is not None:
        params["maxPrice"] = int(max_price)

    query = (query or "").strip()
    if query:
        path = f"{base}/search"
        params["query"] = query
    elif category in _FB_CATEGORY_PATHS:
        section = _FB_CATEGORY_PATHS[category]
        path = f"{base}/{section}" if city else f"{base}/category/{section}"
    else:
        path = base
    return f"{path}?{urlencode(params)}" if params else path


def external_search_links(
    query: Optional[str] = None,
    region: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> List[Dict[str, str]]:
    """One link per platform the user should check by hand for the same search."""
    return [
        {
            "platform": "facebook_marketplace",
            "label": "See matches on Facebook Marketplace",
            "url": facebook_marketplace_url(query, region, category, min_price, max_price),
        },
    ]
