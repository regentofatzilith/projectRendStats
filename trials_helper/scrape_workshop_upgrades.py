"""Scrape workshop upgrade categories from The Tower idle Fandom wiki.

This script extracts the high-level upgrade category listings (Attack / Defense / Utility / Ultimate Weapons
and Enhancement variants) from the Workshop Upgrades page and produces a JSON file with a structured schema.

License note: Source content from Fandom is licensed under CC-BY-SA; extracted factual data (names, level counts)
can be reused but if you include descriptions or verbatim text ensure attribution and share-alike compliance.

Future extensions:
- Follow individual upgrade links to pull scaling formulas and max levels.
- Cache responses locally (avoid hammering the wiki).
- Provide diff mode to detect newly added upgrades.

Usage (PowerShell):
    python scrape_workshop_upgrades.py --out assets/workshop_upgrades.json

"""
from __future__ import annotations
import re
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import requests
from bs4 import BeautifulSoup

SOURCE_URL = "https://the-tower-idle-tower-defense.fandom.com/wiki/Workshop_Upgrades"
CATEGORY_KEYS = [
    "Attack Upgrades", "Defense Upgrades", "Utility Upgrades", "Ultimate Weapons",
    # Enhancement condensed groups sometimes appear separately
    "Attack Enhancement", "Defense Enhancement", "Utility Enhancement"
]

# Regex to split bullet-separated upgrade line (not currently used, retained for future refinement)
SPLIT_PATTERN = re.compile(r"\s*•\s*")

# Some pages list condensed upgrade lines; we capture alphanumeric, spaces, / and +
ITEM_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9+/][A-Za-z0-9 +'/-]*")


def fetch_html(url: str) -> str:
    # Provide a custom user-agent to be polite and avoid generic blocking.
    headers = {"User-Agent": "ProjectAtziScraper/1.0 (+https://github.com/)"}
    resp = requests.get(url, timeout=30, headers=headers)
    resp.raise_for_status()
    return resp.text


def extract_categories(html: str) -> Dict[str, List[str]]:
    soup = BeautifulSoup(html, "html.parser")

    # Collect all text blocks that might contain category lines
    text_blocks: List[str] = []
    for table in soup.find_all("table"):
        text_blocks.append(table.get_text(separator=" ", strip=True))
    for p in soup.find_all(["p", "div"]):
        # Reduce noise by only keeping lines containing one of the category keys
        t = p.get_text(separator=" ", strip=True)
        if any(k in t for k in CATEGORY_KEYS):
            text_blocks.append(t)

    categories: Dict[str, List[str]] = {}
    for block in text_blocks:
        for key in CATEGORY_KEYS:
            if key in block:
                # Example block might look like: "Attack Upgrades | Damage • Attack Speed • Critical Chance"
                # Extract substring after key
                # Split at key then take remainder
                part = block.split(key, 1)[-1]
                # Remove leading separators
                part = part.lstrip(" |:–-")
                # Split on bullet markers
                raw_items = re.split(r"•", part)
                cleaned: List[str] = []
                for item in raw_items:
                    item = item.strip()
                    if not item:
                        continue
                    # Stop if we hit another category name inside the same block
                    if any(other != key and other in item for other in CATEGORY_KEYS):
                        continue
                    # Filter out very short / noise tokens
                    if len(item) < 2:
                        continue
                    # Remove trailing image markers or extraneous words
                    item = re.sub(r"\b(Image|Unlocked|Chance|Level Skip)$", "", item).strip()
                    cleaned.append(item)
                if cleaned:
                    # Deduplicate while preserving order
                    seen = set()
                    unique_items = []
                    for c in cleaned:
                        if c not in seen:
                            seen.add(c)
                            unique_items.append(c)
                    # Merge if category already exists (union)
                    prev = categories.get(key, [])
                    combined = prev + [i for i in unique_items if i not in prev]
                    categories[key] = combined
    return categories


def build_payload(categories: Dict[str, List[str]]) -> Dict:
    return {
        "meta": {
            "source_url": SOURCE_URL,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "category_count": len(categories),
            "total_items": sum(len(v) for v in categories.values()),
            "license": "CC-BY-SA (source: Fandom) - names only, no verbatim descriptions"
        },
        "categories": categories
    }


def main():
    parser = argparse.ArgumentParser(description="Scrape workshop upgrade categories from Fandom wiki.")
    parser.add_argument("--out", type=str, default="workshop_upgrades.json", help="Output JSON file path")
    args = parser.parse_args()

    html = fetch_html(SOURCE_URL)
    categories = extract_categories(html)
    payload = build_payload(categories)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {out_path} with {payload['meta']['category_count']} categories and {payload['meta']['total_items']} items.")


if __name__ == "__main__":
    main()
