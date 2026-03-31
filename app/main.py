import argparse
import csv
import logging
import os

from dotenv import load_dotenv
from camoufox.sync_api import Camoufox

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_PATH = os.path.join(BASE_DIR, "sessions", "session.json")
RESULTS_DIR = os.path.join(BASE_DIR, "data")

CSV_FIELDS = [
    "name",
    "rating",
    "reviews",
    "category",
    "address",
    "phone",
    "website",
    "hours",
    "price_level",
    "plus_code",
]


def check_for_cookie_consent(page):
    logging.debug("Checking for cookie consent form...")
    try:
        if page.locator(
            'form[action="https://consent.google.com/save"]'
        ).first.is_visible(timeout=3000):
            logging.info("Cookie consent form found, accepting...")
            page.locator(
                'form[action="https://consent.google.com/save"] button'
            ).first.click()
            logging.info("Cookie consent accepted")
        else:
            logging.debug("No cookie consent form found")
    except Exception as e:
        logging.error(f"Cookie consent check failed: {e}")


def google_maps_scroll(page):
    logging.info("Starting to scroll results feed...")
    feed = page.locator('div[role="feed"]')
    scroll_count = 0
    while True:
        scroll_count += 1
        feed.evaluate("el => el.scrollBy(0, 4000)")
        logging.debug(f"Scroll #{scroll_count}")
        page.wait_for_timeout(2000)
        if page.locator(".HlvSq").is_visible():
            logging.info(f"Reached end of list after {scroll_count} scrolls")
            break


def extract_place_data(page):
    logging.debug("Extracting place data...")
    data = {}

    fields = [
        ("name", "h1.DUwDvf", "text"),
        ("rating", 'div.F7nice span[aria-hidden="true"]', "text"),
        ("reviews", 'div.F7nice span[aria-label*="reviews"]', "aria-label"),
        ("category", "button.DkEaL", "text"),
        ("address", 'button[data-item-id="address"] div.fontBodyMedium', "text"),
        ("phone", 'button[data-item-id*="phone"] div.fontBodyMedium', "text"),
        ("website", 'a[data-item-id="authority"]', "href"),
        ("hours", "div.t39EBf.GUrTXd[aria-label]", "aria-label"),
        ("price_level", "span.mgr77e span[aria-label]", "text"),
        ("plus_code", 'button[data-item-id="oloc"] div.fontBodyMedium', "text"),
    ]

    for field_name, selector, attr in fields:
        locator = page.locator(selector)
        if locator.count() > 0:
            if attr == "text":
                data[field_name] = locator.first.text_content()
            else:
                data[field_name] = locator.first.get_attribute(attr)
            logging.debug(f"  {field_name}: {data[field_name]}")
        else:
            logging.debug(f"  {field_name}: not found")

    return data


def collect_place_urls(page):
    logging.info("Collecting place URLs from feed...")
    items = page.locator('div[role="feed"] > div > div > a')
    total_items = items.count()
    logging.debug(f"Found {total_items} elements in feed")
    urls = []
    for i in range(total_items):
        href = items.nth(i).get_attribute("href")
        if href:
            urls.append(href)
            logging.debug(f"  URL #{len(urls)}: {href[:80]}...")
        else:
            logging.debug(f"  Item #{i+1}: no href attribute")
    logging.info(f"Collected {len(urls)} place URLs (from {total_items} elements)")
    return urls


def scrape_all_places(browser, page, urls):
    results = []
    count = len(urls)
    logging.info(f"Starting to scrape {count} places...")

    for i, url in enumerate(urls):
        try:
            logging.debug(f"[{i+1}/{count}] Opening: {url[:80]}...")
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            data = extract_place_data(page)
            if data.get("name"):
                results.append(data)
                logging.info(f"[{i+1}/{count}] Scraped: {data['name']}")
            else:
                logging.warning(f"[{i+1}/{count}] No data found at {url[:80]}")
        except Exception as e:
            logging.error(f"[{i+1}/{count}] Error: {e}")
            try:
                page.close()
            except Exception:
                pass
            logging.info("Reopening page after crash...")
            page = browser.new_page(viewport={"width": 1920, "height": 1080})

    logging.info(f"Scraping complete: {len(results)}/{count} places collected")
    return results


def save_to_csv(results, query):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    filename = query.replace(" ", "_").lower() + ".csv"
    filepath = os.path.join(RESULTS_DIR, filename)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(results)
    logging.info(f"Saved {len(results)} places to {filepath}")


def parse_args():
    parser = argparse.ArgumentParser(description="Google Maps Scraper")
    parser.add_argument(
        "-q", "--query",
        default=os.getenv("SEARCH_QUERY", "restaurants in New York"),
        help="Search query (default: from .env or 'restaurants in New York')",
    )
    parser.add_argument(
        "--headless",
        default=os.getenv("HEADLESS", "true").lower() == "true",
        action=argparse.BooleanOptionalAction,
        help="Run browser in headless mode (default: from .env or true)",
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "DEBUG"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (default: from .env or DEBUG)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    query = args.query
    url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"

    logging.info(f"Starting Google Maps scraper for: '{query}'")
    logging.info(f"URL: {url}")
    os.makedirs(os.path.dirname(SESSION_PATH), exist_ok=True)

    with Camoufox(headless=args.headless) as browser:
        logging.info("Browser launched")
        page = browser.new_page(
            storage_state=SESSION_PATH if os.path.exists(SESSION_PATH) else None,
            viewport={"width": 1920, "height": 1080},
        )
        logging.info("Navigating to Google Maps...")
        page.goto(url, wait_until="domcontentloaded")
        logging.info("Page loaded")
        check_for_cookie_consent(page)
        page.wait_for_timeout(2000)
        google_maps_scroll(page)

        urls = collect_place_urls(page)
        results = scrape_all_places(browser, page, urls)
        save_to_csv(results, query)


if __name__ == "__main__":
    main()
