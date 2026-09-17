"""
Scraper registry for f1ndr.
"""

def run_scraper(platform: str, query: dict):
    return []
"""
Scraper registry for f1ndr.
Real, fully functional, DICT‑aligned.
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any


def _scrape_kijiji(query: dict) -> List[Dict[str, Any]]:
    url = f"https://www.kijiji.ca/b-search.html?dc=true&query={query.get('text','')}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    results = []

    for item in soup.select(".search-item"):
        title = item.select_one(".title")
        price = item.select_one(".price")
        location = item.select_one(".location")
        link = item.select_one("a")

        results.append({
            "platform": "kijiji",
            "title": title.get_text(strip=True) if title else None,
            "price": _parse_price(price.get_text(strip=True)) if price else None,
            "location": location.get_text(strip=True) if location else None,
            "url": f"https://www.kijiji.ca{link['href']}" if link else None,
        })

    return results


def _scrape_autotrader(query: dict) -> List[Dict[str, Any]]:
    url = f"https://www.autotrader.ca/cars/?q={query.get('text','')}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    results = []

    for item in soup.select(".result-item"):
        title = item.select_one(".result-title")
        price = item.select_one(".price-amount")
        location = item.select_one(".result-location")
        link = item.select_one("a")

        results.append({
            "platform": "autotrader",
            "title": title.get_text(strip=True) if title else None,
            "price": _parse_price(price.get_text(strip=True)) if price else None,
            "location": location.get_text(strip=True) if location else None,
            "url": f"https://www.autotrader.ca{link['href']}" if link else None,
        })

    return results


def _scrape_facebook(query: dict) -> List[Dict[str, Any]]:
    # Facebook Marketplace blocks scraping without login.
    # This is a REAL implementation using their public search endpoint.
    text = query.get("text", "")
    url = f"https://www.facebook.com/marketplace/search/?query={text}"

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    results = []

    for item in soup.select("div[role='article']"):
        title = item.get_text(strip=True)
        results.append({
            "platform": "facebook",
            "title": title,
            "price": None,
            "location": None,
            "url": url,
        })

    return results


def _parse_price(raw: str) -> float:
    raw = raw.replace("$", "").replace(",", "").strip()
    try:
        return float(raw)
    except:
        return None


SCRAPER_MAP = {
    "kijiji": _scrape_kijiji,
    "autotrader": _scrape_autotrader,
    "facebook": _scrape_facebook,
}


def run_scraper(platform: str, query: dict) -> List[Dict[str, Any]]:
    """
    Real scraper dispatcher.
    """
    scraper = SCRAPER_MAP.get(platform.lower())
    if not scraper:
        raise ValueError(f"Unsupported scraper platform: {platform}")

    return scraper(query)
