"""RV/towable subcategory sets and field validation.

Shared by the API schema layer (VehicleIn) and module-side validation; keep it
free of api imports so dependency direction stays modules-down.
"""

from typing import Any, Dict, Optional

TOWABLE_SUBCATEGORIES = {"travel_trailer", "fifth_wheel", "toy_hauler", "truck_camper"}
MOTORIZED_RV_SUBCATEGORIES = {"motorhome_a", "motorhome_b", "motorhome_c"}
RV_SUBCATEGORIES = TOWABLE_SUBCATEGORIES | MOTORIZED_RV_SUBCATEGORIES

HITCH_TYPES = {"bumper_pull", "fifth_wheel", "gooseneck", "truck_bed", "none"}

# Fields that only make sense on a motorized unit.
_MOTORIZED_ONLY = ("mileage", "engine", "chassis")


def validate_rv_fields(doc: Dict[str, Any]) -> Optional[str]:
    """Return an error message when RV/towable field rules are violated, else None."""
    subcategory = doc.get("subcategory")
    if subcategory in TOWABLE_SUBCATEGORIES:
        bad = [f for f in _MOTORIZED_ONLY if doc.get(f) is not None]
        if bad:
            return "Towable units cannot specify mileage, engine, or chassis"
    gvwr, dry = doc.get("gvwr_lbs"), doc.get("dry_weight_lbs")
    if gvwr is not None and dry is not None and gvwr < dry:
        return "gvwr_lbs must not be less than dry_weight_lbs"
    return None
