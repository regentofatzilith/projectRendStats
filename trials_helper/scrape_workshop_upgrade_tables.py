"""Scrape per-level workshop upgrade tables (Level / Value / Cost / Total Cost) from The Tower Idle wiki.

Overview:
  1. Fetch the main Workshop Upgrades page to discover all upgrade item links grouped by category.
  2. For each item page, locate the upgrade table whose headers include the required columns.
  3. Parse every row into a structured list with numeric normalization helpers.
  4. Emit a JSON file containing metadata and full per-level data for downstream analytics.

Usage (PowerShell):
    python scrape_workshop_upgrade_tables.py --out assets/workshop_upgrades_tables.json
    python scrape_workshop_upgrade_tables.py --limit 5  # quick smoke test

Notes:
  - Source content is licensed CC-BY-SA; this script extracts factual numeric data (levels, costs).
  - Be polite: there's a short sleep between requests; consider --limit for development.
  - Some pages may lack a table or have variant formatting; they will be recorded with an error.

Potential future enhancements:
  - Retry & exponential backoff on transient network errors.
  - Local caching layer (ETag/Last-Modified) to avoid repeated full downloads.
  - Cost curve analytics (incremental vs cumulative validation).
  - Merge with enhancements data set.
"""
from __future__ import annotations
import argparse
import json
import math
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://the-tower-idle-tower-defense.fandom.com"
WORKSHOP_URL = f"{BASE_URL}/wiki/Workshop_Upgrades"

HEADERS = {"User-Agent": "ProjectAtziWorkshopScraper/1.0 (+https://github.com/)"}

# Recognize common large number suffixes used on wiki pages.
SUFFIX_MAP = {
    'K': 1e3, 'M': 1e6, 'B': 1e9, 'T': 1e12,
    'Qa': 1e15, 'Qi': 1e18, 'Sx': 1e21, 'Sp': 1e24,
    'Oc': 1e27, 'No': 1e30, 'Dc': 1e33
}

NUM_CLEAN_RE = re.compile(r"[^0-9A-Za-z.+/%]" )
PERCENT_RE = re.compile(r"([0-9.+]+)\s*%")

TABLE_HEADER_KEYS = {"level", "value", "cost", "total cost"}

# Manual fallback data for Free Attack Upgrade (provided externally) when no table is located.
# Columns: Level, Value(percentage), Coins (cost), Total Coins (cumulative cost)
FREE_ATTACK_FALLBACK = [
    (1, "0.50%", "75", "75"), (2, "1.00%", "118", "193"), (3, "1.50%", "171", "364"),
    (4, "2.00%", "236", "600"), (5, "2.50%", "314", "914"), (6, "3.00%", "407", "1.32K"),
    (7, "3.50%", "515", "1.84K"), (8, "4.00%", "639", "2.48K"), (9, "4.50%", "781", "3.26K"),
    (10, "5.00%", "941", "4.20K"), (11, "5.50%", "1.12K", "5.32K"), (12, "6.00%", "1.32K", "6.63K"),
    (13, "6.50%", "1.53K", "8.16K"), (14, "7.00%", "1.77K", "9.93K"), (15, "7.50%", "2.03K", "11.96K"),
    (16, "8.00%", "2.30K", "14.26K"), (17, "8.50%", "2.60K", "16.86K"), (18, "9.00%", "2.92K", "19.79K"),
    (19, "9.50%", "3.27K", "23.05K"), (20, "10.00%", "3.63K", "26.69K"), (21, "10.50%", "4.02K", "30.71K"),
    (22, "11.00%", "4.43K", "35.14K"), (23, "11.50%", "4.87K", "40.01K"), (24, "12.00%", "5.33K", "45.34K"),
    (25, "12.50%", "5.81K", "51.15K"), (26, "13.00%", "6.32K", "57.47K"), (27, "13.50%", "6.85K", "64.33K"),
    (28, "14.00%", "7.41K", "71.74K"), (29, "14.50%", "8.00K", "79.73K"), (30, "15.00%", "8.60K", "88.34K"),
    (31, "15.50%", "9.24K", "97.58K"), (32, "16.00%", "9.90K", "107.48K"), (33, "16.50%", "10.59K", "118.06K"),
    (34, "17.00%", "11.30K", "129.36K"), (35, "17.50%", "12.04K", "141.41K"), (36, "18.00%", "12.81K", "154.22K"),
    (37, "18.50%", "13.61K", "167.82K"), (38, "19.00%", "14.43K", "182.25K"), (39, "19.50%", "15.28K", "197.53K"),
    (40, "20.00%", "16.16K", "213.69K"), (41, "20.50%", "17.07K", "230.75K"), (42, "21.00%", "18.00K", "248.75K"),
    (43, "21.50%", "18.96K", "267.72K"), (44, "22.00%", "19.96K", "287.67K"), (45, "22.50%", "20.98K", "308.65K"),
    (46, "23.00%", "22.03K", "330.68K"), (47, "23.50%", "23.11K", "353.79K"), (48, "24.00%", "24.22K", "378.01K"),
    (49, "24.50%", "25.36K", "403.37K"), (50, "25.00%", "26.53K", "429.90K"), (51, "25.50%", "28.56K", "458.46K"),
    (52, "26.00%", "29.83K", "488.29K"), (53, "26.50%", "31.13K", "519.41K"), (54, "27.00%", "32.46K", "551.87K"),
    (55, "27.50%", "33.82K", "585.69K"), (56, "28.00%", "35.21K", "620.90K"), (57, "28.50%", "36.64K", "657.54K"),
    (58, "29.00%", "38.10K", "695.63K"), (59, "29.50%", "39.59K", "735.22K"), (60, "30.00%", "41.11K", "776.33K"),
    (61, "30.50%", "42.67K", "818.99K"), (62, "31.00%", "44.25K", "863.25K"), (63, "31.50%", "45.88K", "909.12K"),
    (64, "32.00%", "47.53K", "956.66K"), (65, "32.50%", "49.22K", "1.01M"), (66, "33.00%", "50.94K", "1.06M"),
    (67, "33.50%", "52.70K", "1.11M"), (68, "34.00%", "54.49K", "1.16M"), (69, "34.50%", "56.31K", "1.22M"),
    (70, "35.00%", "58.17K", "1.28M"), (71, "35.50%", "60.06K", "1.34M"), (72, "36.00%", "61.99K", "1.40M"),
    (73, "36.50%", "63.95K", "1.46M"), (74, "37.00%", "65.94K", "1.53M"), (75, "37.50%", "67.97K", "1.60M"),
    (76, "38.00%", "73.54K", "1.67M"), (77, "38.50%", "75.75K", "1.75M"), (78, "39.00%", "77.99K", "1.83M"),
    (79, "39.50%", "80.27K", "1.91M"), (80, "40.00%", "82.59K", "1.99M"), (81, "40.50%", "84.94K", "2.07M"),
    (82, "41.00%", "87.33K", "2.16M"), (83, "41.50%", "89.76K", "2.25M"), (84, "42.00%", "92.23K", "2.34M"),
    (85, "42.50%", "94.74K", "2.44M"), (86, "43.00%", "97.28K", "2.53M"), (87, "43.50%", "99.86K", "2.63M"),
    (88, "44.00%", "102.48K", "2.74M"), (89, "44.50%", "105.14K", "2.84M"), (90, "45.00%", "107.84K", "2.95M"),
    (91, "45.50%", "110.57K", "3.06M"), (92, "46.00%", "113.35K", "3.17M"), (93, "46.50%", "116.16K", "3.29M"),
    (94, "47.00%", "119.02K", "3.41M"), (95, "47.50%", "121.91K", "3.53M"), (96, "48.00%", "124.84K", "3.66M"),
    (97, "48.50%", "127.81K", "3.78M"), (98, "49.00%", "130.82K", "3.91M"), (99, "49.50%", "133.87K", "4.05M"),
]


@dataclass
class LevelRow:
    level: int
    value_raw: str
    value: Optional[float]
    cost_raw: str
    cost: Optional[float]
    total_cost_raw: str
    total_cost: Optional[float]

@dataclass
class ItemData:
    name: str
    slug: str
    category: str
    url: str
    levels: List[LevelRow]
    errors: List[str]
    table_headers: List[str]


def fetch(url: str) -> str:
    resp = requests.get(url, timeout=30, headers=HEADERS)
    resp.raise_for_status()
    return resp.text


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip('_')


def parse_number(text: str) -> Optional[float]:
    if text is None:
        return None
    t = text.strip()
    if not t or t in {'-', '—'}:
        return None
    # Percent handling
    pm = PERCENT_RE.search(t)
    if pm and pm.group(1):
        try:
            return float(pm.group(1)) / 100.0
        except ValueError:
            pass
    # Strip commas & spaces
    t = t.replace(',', '').replace(' ', '')
    # Direct float/int
    try:
        return float(t)
    except ValueError:
        pass
    # Suffix variant (e.g., 1.23Qa)
    m = re.match(r"([0-9]*\.?[0-9]+)([A-Za-z]+)$", t)
    if m:
        base, suffix = m.groups()
        mult = SUFFIX_MAP.get(suffix)
        if mult:
            try:
                return float(base) * mult
            except ValueError:
                return None
    return None


def find_main_table(soup: BeautifulSoup):  # returns Tag or None
    # Identify the primary workshop table via header text.
    for table in soup.find_all('table', class_='wikitable'):
        header = table.find('th')
        if header and 'Workshop Upgrades' in header.get_text():
            return table
    return None


def extract_item_links(base_html: str) -> Dict[str, List[Tuple[str, str]]]:
    soup = BeautifulSoup(base_html, 'html.parser')
    main_table = find_main_table(soup)
    results: Dict[str, List[Tuple[str, str]]] = {}
    if not main_table:
        return results
    for row in main_table.find_all('tr')[1:]:  # skip header row
        cols = row.find_all('td')
        if len(cols) != 2:
            continue
        category_anchor = cols[0].find('a')
        if not category_anchor:
            continue
        category = category_anchor.get_text(strip=True)
        items: List[Tuple[str, str]] = []
        for a in cols[1].find_all('a'):
            name = a.get_text(strip=True)
            href_attr = a.get('href')
            href = str(href_attr) if href_attr else None
            if not href or href.startswith('#'):
                continue
            # Filter out anchors that are the category itself or duplicates.
            if name.lower() == category.lower():
                continue
            abs_url = href if href.startswith('http') else f"{BASE_URL}{href}"
            items.append((name, abs_url))
        if items:
            results[category] = items
    return results


def locate_upgrade_table(soup: BeautifulSoup):  # returns Tag or None
    # Look for a table that has required headers subset.
    for table in soup.find_all('table'):
        headers = [th.get_text(strip=True).lower() for th in table.find_all('th')]
        if not headers:
            continue
        header_set = set(headers)
        # Must include at least Level & Cost; Value and Total Cost often present.
        if 'level' in header_set and 'cost' in header_set:
            return table
    return None


def parse_item_table(html: str, name: str, category: str, url: str) -> ItemData:
    soup = BeautifulSoup(html, 'html.parser')
    table = locate_upgrade_table(soup)
    errors: List[str] = []
    levels: List[LevelRow] = []
    headers_lower: List[str] = []
    if not table:
        # Fallback: Free Attack Upgrade manual data injection
        if url.endswith('/wiki/Free_Upgrades') and name == 'Free Attack Upgrade':
            for lvl, val_raw, cost_raw, total_raw in FREE_ATTACK_FALLBACK:
                levels.append(LevelRow(
                    level=lvl,
                    value_raw=val_raw,
                    value=parse_number(val_raw),
                    cost_raw=cost_raw,
                    cost=parse_number(cost_raw),
                    total_cost_raw=total_raw,
                    total_cost=parse_number(total_raw)
                ))
            headers_lower = ['level', 'value', 'cost', 'total cost']
            return ItemData(name=name, slug=slugify(name), category=category, url=url, levels=levels, errors=[], table_headers=headers_lower)
        # Attempt structured free upgrades parsing (shared tables with Level/Value/Coins/Total Coins)
        if url.endswith('/wiki/Free_Upgrades') and name.startswith('Free '):
            # Enhanced logic: accept tables with Level & Coins headers; 'value' may vary or be absent.
            free_tables = []
            for t in soup.find_all('table'):
                h = [th.get_text(strip=True).lower() for th in t.find_all('th')]
                if 'level' in h and 'coins' in h:  # relaxed requirement
                    free_tables.append((t, h))
            key = name.split()[1].lower()  # attack/defense/utility
            selected = None
            if free_tables:
                if len(free_tables) == 1:
                    selected = free_tables[0]
                else:
                    # Score tables by proximity of preceding text containing the key.
                    scored = []
                    for t, h in free_tables:
                        prev_text = ''
                        # Walk back a few siblings to gather context.
                        ctx_nodes = []
                        prev = t.previous_sibling
                        steps = 0
                        while prev and steps < 8:
                            if getattr(prev, 'get_text', None):
                                ctx_nodes.append(prev.get_text(strip=True).lower())
                            prev = prev.previous_sibling
                            steps += 1
                        prev_text = ' '.join(ctx_nodes)
                        score = 1 if key in prev_text else 0
                        scored.append((score, t, h))
                    scored.sort(reverse=True, key=lambda x: x[0])
                    # Choose highest score, fallback first table.
                    selected = (scored[0][1], scored[0][2]) if scored else free_tables[0]
            if selected:
                t, h = selected
                headers_lower = h
                # Determine indices.
                def idx_exact(col: str):
                    for i, hh in enumerate(h):
                        if col == hh:
                            return i
                    return None
                level_idx = idx_exact('level')
                cost_idx = idx_exact('coins')
                total_idx = idx_exact('total coins')
                value_idx = idx_exact('value')
                # If no explicit value header, heuristically choose first non-level/non-cost column.
                if value_idx is None:
                    for i, hh in enumerate(h):
                        if i not in {level_idx, cost_idx, total_idx}:
                            value_idx = i
                            break
                for r in t.find_all('tr')[1:]:
                    cells = r.find_all(['td','th'])
                    if not cells or level_idx is None or cost_idx is None:
                        continue
                    try:
                        lv_raw = cells[level_idx].get_text(strip=True)
                        lv = int(re.sub(r"[^0-9]","", lv_raw))
                    except ValueError:
                        continue
                    val_raw = cells[value_idx].get_text(strip=True) if (value_idx is not None and value_idx < len(cells)) else ''
                    cost_raw = cells[cost_idx].get_text(strip=True)
                    total_raw = cells[total_idx].get_text(strip=True) if (total_idx is not None and total_idx < len(cells)) else ''
                    levels.append(LevelRow(
                        level=lv,
                        value_raw=val_raw,
                        value=parse_number(val_raw),
                        cost_raw=cost_raw,
                        cost=parse_number(cost_raw),
                        total_cost_raw=total_raw,
                        total_cost=parse_number(total_raw)
                    ))
                if levels:
                    return ItemData(name=name, slug=slugify(name), category=category, url=url, levels=levels, errors=[], table_headers=headers_lower)
        errors.append('No suitable table found')
        return ItemData(name=name, slug=slugify(name), category=category, url=url, levels=levels, errors=errors, table_headers=headers_lower)
    header_cells = table.find_all('th')
    headers = [hc.get_text(strip=True) for hc in header_cells]
    headers_lower = [h.lower() for h in headers]
    # Identify column indices.
    def find_idx(key: str) -> Optional[int]:
        for i, h in enumerate(headers_lower):
            if key == h:
                return i
        # Allow partial match (e.g., Total Cost vs Total cost).
        for i, h in enumerate(headers_lower):
            if key in h:
                return i
        return None
    level_idx = find_idx('level')
    value_idx = find_idx('value')
    cost_idx = find_idx('cost')
    total_cost_idx = find_idx('total cost')
    if level_idx is None or cost_idx is None:
        errors.append('Missing mandatory Level or Cost columns')
        return ItemData(name=name, slug=slugify(name), category=category, url=url, levels=levels, errors=errors, table_headers=headers_lower)
    for r in table.find_all('tr')[1:]:  # skip header row
        cells = r.find_all(['td', 'th'])
        if len(cells) < 2:
            continue
        try:
            level_raw = cells[level_idx].get_text(strip=True)
            if not level_raw:
                continue
            level = int(re.sub(r"[^0-9]", "", level_raw))
        except ValueError:
            continue
        value_raw = cells[value_idx].get_text(strip=True) if value_idx is not None else ''
        cost_raw = cells[cost_idx].get_text(strip=True)
        total_raw = cells[total_cost_idx].get_text(strip=True) if total_cost_idx is not None else ''
        value_num = parse_number(value_raw)
        cost_num = parse_number(cost_raw)
        total_num = parse_number(total_raw) if total_raw else None
        levels.append(LevelRow(
            level=level,
            value_raw=value_raw,
            value=value_num,
            cost_raw=cost_raw,
            cost=cost_num,
            total_cost_raw=total_raw,
            total_cost=total_num
        ))
    if not levels:
        errors.append('Parsed 0 level rows')
    return ItemData(name=name, slug=slugify(name), category=category, url=url, levels=levels, errors=errors, table_headers=headers_lower)


def build_payload(items: List[ItemData], link_map: Dict[str, List[Tuple[str, str]]]) -> Dict:
    return {
        'meta': {
            'source_index_url': WORKSHOP_URL,
            'retrieved_at': datetime.now(timezone.utc).isoformat(),
            'item_count': len(items),
            'category_count': len(link_map),
            'license': 'CC-BY-SA (source: Fandom) - numeric factual data only',
            'errors_count': sum(1 for i in items if i.errors)
        },
        'categories': {
            cat: [name for name, _ in link_map[cat]] for cat in link_map
        },
        'items': [
            {
                **{k: v for k, v in asdict(item).items() if k not in {'levels'}},
                'levels': [asdict(lr) for lr in item.levels]
            } for item in items
        ]
    }


def main():
    parser = argparse.ArgumentParser(description='Scrape per-level workshop upgrade tables.')
    parser.add_argument('--out', type=str, default='assets/workshop_upgrades_tables.json', help='Output JSON path')
    parser.add_argument('--limit', type=int, default=None, help='Optional limit on number of items (for testing)')
    parser.add_argument('--delay', type=float, default=0.75, help='Delay seconds between item requests')
    parser.add_argument('--only-names', type=str, default=None, help='Comma-separated list of item names to scrape (partial update)')
    args = parser.parse_args()

    index_html = fetch(WORKSHOP_URL)
    link_map = extract_item_links(index_html)
    all_links: List[Tuple[str, str, str]] = []  # (category, name, url)
    for cat, entries in link_map.items():
        for name, url in entries:
            all_links.append((cat, name, url))
    if args.only_names:
        target_names = {n.strip() for n in args.only_names.split(',') if n.strip()}
        all_links = [tpl for tpl in all_links if tpl[1] in target_names]
    if args.limit:
        all_links = all_links[:args.limit]
    items: List[ItemData] = []
    for i, (cat, name, url) in enumerate(all_links, 1):
        try:
            html = fetch(url)
        except Exception as e:
            items.append(ItemData(name=name, slug=slugify(name), category=cat, url=url, levels=[], errors=[f'Fetch error: {e}'], table_headers=[]))
            continue
        item_data = parse_item_table(html, name=name, category=cat, url=url)
        items.append(item_data)
        print(f"[{i}/{len(all_links)}] {name}: rows={len(item_data.levels)} errors={'|'.join(item_data.errors) if item_data.errors else 'none'}")
        time.sleep(args.delay)

    payload = build_payload(items, link_map)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {out_path} with {payload['meta']['item_count']} items; errors={payload['meta']['errors_count']}")


if __name__ == '__main__':
    main()
