"""
Bluetti AC200L Price Monitor
Checks the product price once and shows a popup alert if it's at or below $700.

Run manually:  python price_monitor.py
Scheduled:     pythonw price_monitor.py  (no console window)
"""

import csv
import datetime
import json
import os
import sys

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Configuration — edit these if needed
# ---------------------------------------------------------------------------

PRODUCT_URL = (
    "https://www.bluettipower.com/products/"
    "ac200l-portable-power-station?variant=46352232349915"
)
SHOPIFY_JSON_URL = (
    "https://www.bluettipower.com/products/ac200l-portable-power-station.json"
)
VARIANT_ID = 46352232349915
PRICE_THRESHOLD = 700.00
PRODUCT_NAME = "Bluetti AC200L Portable Power Station"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, "price_monitor.log")
HISTORY_FILE = os.path.join(SCRIPT_DIR, "price_history.csv")

REQUEST_TIMEOUT = 15
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
    ),
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "en-US,en;q=0.9",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def append_history(price, below_threshold, source):
    file_exists = os.path.isfile(HISTORY_FILE)
    with open(HISTORY_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "price_usd", "below_threshold", "source"])
        writer.writerow([
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            f"{price:.2f}",
            str(below_threshold),
            source,
        ])


def parse_price(raw):
    """Convert a Shopify price value to a float dollar amount."""
    if isinstance(raw, str):
        return float(raw.replace(",", "").strip())
    value = float(raw)
    # Shopify Admin API returns cents (e.g. 69900); storefront returns dollars ("699.00")
    return value / 100.0 if value > 10_000 else value

# ---------------------------------------------------------------------------
# Fetch strategies
# ---------------------------------------------------------------------------

def fetch_via_shopify_json():
    """Strategy 1: Shopify storefront .json endpoint. Returns (price, source) or None."""
    try:
        response = requests.get(SHOPIFY_JSON_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        log(f"Shopify JSON fetch failed: {exc}")
        return None

    try:
        data = response.json()
    except ValueError as exc:
        log(f"Shopify JSON parse error: {exc}")
        return None

    variants = data.get("product", {}).get("variants", [])
    if not variants:
        log("Shopify JSON: no variants found")
        return None

    # Match the specific variant; fall back to first variant
    target = next((v for v in variants if v.get("id") == VARIANT_ID), variants[0])
    raw_price = target.get("price")
    if raw_price is None:
        log("Shopify JSON: no price field in variant")
        return None

    try:
        return parse_price(raw_price), "shopify_json"
    except (ValueError, TypeError) as exc:
        log(f"Shopify JSON price parse error: {exc}")
        return None


def fetch_via_html_scrape():
    """Strategy 2: Scrape product page HTML and find JSON-LD structured data. Returns (price, source) or None."""
    try:
        response = requests.get(PRODUCT_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        log(f"HTML page fetch failed: {exc}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    for script in soup.find_all("script", type="application/ld+json"):
        if not script.string:
            continue
        try:
            data = json.loads(script.string)
        except json.JSONDecodeError:
            continue

        if isinstance(data, list):
            data = next((d for d in data if d.get("@type") == "Product"), None)
            if data is None:
                continue

        if data.get("@type") != "Product":
            continue

        offers = data.get("offers", {})
        if isinstance(offers, list):
            offers = offers[0]

        raw_price = offers.get("price")
        if raw_price is None:
            continue

        try:
            return parse_price(raw_price), "html_jsonld"
        except (ValueError, TypeError) as exc:
            log(f"HTML JSON-LD price parse error: {exc}")
            continue

    log("HTML scrape: no valid JSON-LD Product block with price found")
    return None

# ---------------------------------------------------------------------------
# Notification
# ---------------------------------------------------------------------------

def show_popup(price):
    """Show a blocking warning popup using tkinter (built into Python on Windows)."""
    try:
        import tkinter as tk
        from tkinter import messagebox
    except ImportError:
        log("tkinter not available — cannot show popup")
        return

    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        messagebox.showwarning(
            title="Price Alert — Bluetti AC200L!",
            message=(
                f"{PRODUCT_NAME}\n\n"
                f"Current price:  ${price:.2f}\n"
                f"Your threshold: ${PRICE_THRESHOLD:.2f}\n\n"
                f"Buy now:\n{PRODUCT_URL}"
            ),
        )
        root.destroy()
    except Exception as exc:
        log(f"Popup error: {exc}")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    log("--- Price check starting ---")

    result = fetch_via_shopify_json()
    if result is None:
        log("Falling back to HTML scrape strategy")
        result = fetch_via_html_scrape()

    if result is None:
        log("ERROR: all fetch strategies failed; cannot determine current price")
        return 1

    price, source = result
    below = price <= PRICE_THRESHOLD

    log(
        f"Price: ${price:.2f} (source: {source}) — "
        f"{'BELOW' if below else 'above'} ${PRICE_THRESHOLD:.2f} threshold"
    )
    append_history(price, below, source)

    if below:
        log(f"ALERT: ${price:.2f} is at or below your ${PRICE_THRESHOLD:.2f} threshold!")
        show_popup(price)
    else:
        log("No alert: price is above threshold")

    log("--- Price check complete ---")
    return 0


if __name__ == "__main__":
    sys.exit(main())
