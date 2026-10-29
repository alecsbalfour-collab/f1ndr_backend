"""
Supported Canadian regions and per-platform URL parameters.

Each region carries display metadata plus a `platforms` map: presence of a
platform key means the scraper can serve that region; its value holds the
template kwargs the scraper's base_url/search_url are formatted with
(e.g. Kijiji {city}/{loc}, Craigslist {sub}, AutoTrader {prov}/{city}).

used.ca city sites (usedcalgary.com ...) only exist in _USED_CITIES; rentfaster
is Alberta-only. used/ebay serve every region (empty param dict).
"""

from typing import Dict, List, Optional

DEFAULT_REGION = "calgary"

# Used.ca city-site hosts, keyed by region slug (no site -> scraper unavailable).
_USED_CITIES = {
    "calgary": "usedcalgary.com",
    "edmonton": "usededmonton.com",
    "victoria": "usedvictoria.com",
    "vancouver": "usedvancouver.com",
    "ottawa": "usedottawa.com",
    "regina": "usedregina.com",
    "halifax": "usedhalifax.com",
}

_ALBERTA = ("calgary", "edmonton", "red_deer", "lethbridge")


def _region(slug: str, label: str, prov: str, province_name: str,
            *, kijiji_city: Optional[str] = None, kijiji_loc: Optional[str] = None,
            cl_sub: Optional[str] = None, locanto_sub: Optional[str] = None,
            at_city: Optional[str] = None, city_path: Optional[str] = None,
            zillow_slug: Optional[str] = None) -> dict:
    """Assemble one region's platform map from per-site parameters."""
    prov_u = prov.upper()
    platforms: Dict[str, dict] = {"used": {}, "ebay": {}}
    if kijiji_city and kijiji_loc:
        platforms["kijiji"] = {"city": kijiji_city, "loc": kijiji_loc}
    if cl_sub:
        platforms["craigslist"] = {"sub": cl_sub}
    if at_city:
        platforms["autotrader"] = {
            "prov": prov, "city": at_city, "prv": province_name,
            "loc": f"{label}%2C%20{prov_u}",
        }
    if locanto_sub:
        platforms["locanto"] = {"sub": locanto_sub}
    if city_path:
        platforms["realtor"] = {"prov": prov, "city": city_path}
        platforms["rentals"] = {"city": city_path}
    if slug in _ALBERTA and city_path:
        platforms["rentfaster"] = {"prov": prov, "city": city_path}
    if zillow_slug:
        platforms["zillow"] = {"cityslug": zillow_slug}
    if slug in _USED_CITIES:
        platforms["usedca"] = {"host": _USED_CITIES[slug]}
        platforms["neighbourhood"] = {"host": _USED_CITIES[slug]}
    return {
        "slug": slug,
        "label": label,
        "province": prov,
        "province_name": province_name,
        "platforms": platforms,
    }


REGIONS: Dict[str, dict] = {
    r["slug"]: r
    for r in [
        _region("calgary", "Calgary", "ab", "Alberta",
                kijiji_city="calgary", kijiji_loc="l1700199", cl_sub="calgary",
                locanto_sub="calgary", at_city="calgary", city_path="calgary",
                zillow_slug="calgary-ab"),
        _region("edmonton", "Edmonton", "ab", "Alberta",
                kijiji_city="edmonton", kijiji_loc="l1700203", cl_sub="edmonton",
                locanto_sub="edmonton", at_city="edmonton", city_path="edmonton",
                zillow_slug="edmonton-ab"),
        _region("red_deer", "Red Deer", "ab", "Alberta",
                kijiji_city="red-deer", kijiji_loc="l1700136",
                at_city="red-deer", city_path="red-deer",
                zillow_slug="red-deer-ab"),
        _region("lethbridge", "Lethbridge", "ab", "Alberta",
                kijiji_city="lethbridge", kijiji_loc="l1700230", cl_sub="lethbridge",
                at_city="lethbridge", city_path="lethbridge",
                zillow_slug="lethbridge-ab"),
        _region("vancouver", "Vancouver", "bc", "British Columbia",
                kijiji_city="vancouver", kijiji_loc="l1700287", cl_sub="vancouver",
                locanto_sub="vancouver", at_city="vancouver", city_path="vancouver",
                zillow_slug="vancouver-bc"),
        _region("victoria", "Victoria", "bc", "British Columbia",
                kijiji_city="victoria", kijiji_loc="l1700173", cl_sub="victoria",
                locanto_sub="victoria", at_city="victoria", city_path="victoria",
                zillow_slug="victoria-bc"),
        _region("toronto", "Toronto", "on", "Ontario",
                kijiji_city="city-of-toronto", kijiji_loc="l1700273", cl_sub="toronto",
                locanto_sub="toronto", at_city="toronto", city_path="toronto",
                zillow_slug="toronto-on"),
        _region("ottawa", "Ottawa", "on", "Ontario",
                kijiji_city="ottawa", kijiji_loc="l1700185", cl_sub="ottawa",
                locanto_sub="ottawa", at_city="ottawa", city_path="ottawa",
                zillow_slug="ottawa-on"),
        _region("montreal", "Montreal", "qc", "Quebec",
                kijiji_city="montreal", kijiji_loc="l1700281", cl_sub="montreal",
                locanto_sub="montreal", at_city="montreal", city_path="montreal",
                zillow_slug="montreal-qc"),
        _region("winnipeg", "Winnipeg", "mb", "Manitoba",
                kijiji_city="winnipeg", kijiji_loc="l1700192", cl_sub="winnipeg",
                locanto_sub="winnipeg", at_city="winnipeg", city_path="winnipeg",
                zillow_slug="winnipeg-mb"),
        _region("saskatoon", "Saskatoon", "sk", "Saskatchewan",
                kijiji_city="saskatoon", kijiji_loc="l1700197", cl_sub="saskatoon",
                at_city="saskatoon", city_path="saskatoon",
                zillow_slug="saskatoon-sk"),
        _region("regina", "Regina", "sk", "Saskatchewan",
                kijiji_city="regina", kijiji_loc="l1700196", cl_sub="regina",
                locanto_sub="regina", at_city="regina", city_path="regina",
                zillow_slug="regina-sk"),
        _region("halifax", "Halifax", "ns", "Nova Scotia",
                kijiji_city="halifax", kijiji_loc="l1700310", cl_sub="halifax",
                locanto_sub="halifax", at_city="halifax", city_path="halifax",
                zillow_slug="halifax-ns"),
    ]
}


def normalize_region(region: Optional[str]) -> str:
    """Slug a region input to a supported key; default when absent."""
    slug = DEFAULT_REGION if region in (None, "") else str(region).strip().lower().replace(" ", "_")
    if slug not in REGIONS:
        raise ValueError(
            f"Unsupported region: {region!r}. Supported: {', '.join(REGIONS)}"
        )
    return slug


def get_region_info(region: str) -> dict:
    return REGIONS[normalize_region(region)]


def list_regions() -> List[dict]:
    return [
        {
            "slug": info["slug"],
            "label": info["label"],
            "province": info["province"],
            "platforms": sorted(info["platforms"]),
        }
        for info in REGIONS.values()
    ]


def platforms_for_region(region: str) -> List[str]:
    return sorted(get_region_info(region)["platforms"])
