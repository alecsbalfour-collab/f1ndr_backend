from playwright.sync_api import sync_playwright
from typing import Optional


class BaseScraper:
    def fetch_html(self, url: str) -> Optional[str]:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="networkidle")
                html = page.content()
                browser.close()
                return html
        except Exception:
            return None



