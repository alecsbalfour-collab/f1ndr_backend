from .field_maps_unifier import FIELD_MAPS_UNIFIER


def _first(raw: dict, keys: list):
    return next((raw[k] for k in keys if raw.get(k) is not None), None)


def unify_listing(raw: dict) -> dict:
    unified = {field: _first(raw, keys) for field, keys in FIELD_MAPS_UNIFIER.items()}
    unified.update({
        "platform": raw.get("platform"),
        "url": raw.get("url"),
        "images": raw.get("images") or [],
        "posted_at": raw.get("posted_at"),
        "raw": raw,
    })
    return unified


class ListingUnifier:
    def unify(self, listing: dict) -> dict:
        return unify_listing(listing)

listing_unifier = ListingUnifier()
