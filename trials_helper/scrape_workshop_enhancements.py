"""Scrape Workshop Enhancement pages (Attack / Defense / Utility) for level tables.

For each enhancement (e.g. Damage, Rend Max, Critical Factor) we attempt to retrieve:
- Description text
- Sample level rows (Level, Value, Coins, Total Coins) available in static HTML
- Inferred scaling formula (value_start, increment per level, max level) when detectable

NOTE: Many Fandom pages may use collapsible tables or dynamically loaded content. This script only parses
what is present in the static HTML response. If full 400-level tables are not embedded, we keep the visible sample.

Inference heuristics:
- Look for pattern: "starts at 1x" or "Starts at 1x" => base value
- Look for pattern: "increases by 0.01x per level" => increment
- Look for pattern: "max of 400 levels" or "max of 400" => max_level
- Construct formula: value(level) = base + increment * level (with small adjustments if description implies inclusive start)

Usage (PowerShell):
    python scrape_workshop_enhancements.py --out assets/workshop_enhancements.json --limit attack

Options:
    --limit {attack,defense,utility,all} to restrict which category set is scraped.

"""
from __future__ import annotations
import re
import json
import time
import argparse
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict
from pathlib import Path
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://the-tower-idle-tower-defense.fandom.com/wiki/Workshop_Enhancement/"
HEADERS = {"User-Agent": "ProjectAtziEnhancementsScraper/1.0 (+https://github.com/)"}

# Enhancement names (initial subset – extend as needed)
ATTACK_ENHANCEMENTS = ["Damage", "Rend Max", "Critical Factor", "Damage/Meter", "Super Crit Multi"]  # fallback
DEFENSE_ENHANCEMENTS = ["Health", "Health Regen", "Wall Health", "Land Mine Damage", "Defense Absolute", "Orbs Size"]  # fallback
UTILITY_ENHANCEMENTS = ["Cash Bonus", "Coin Bonus", "Cells/Kill Bonus", "Free Upgrades", "Recovery Packages", "Enemy Level Skip"]  # fallback

# Normalize enhancement name to URL path segment.
# Example: "Damage/Meter" -> "Attack/Damage/Meter" page? Empirically screenshot shows path pattern like
# /Workshop_Enhancement/Attack/Damage
# Multi-word may simply join with '_' except '/' which becomes '/'. We attempt both patterns.

def build_attack_url(name: str) -> List[str]:
    # Primary pattern
    base = name.replace(" ", "_")
    # Slash remains slash inside path (Damage/Meter)
    return [f"{BASE_URL}Attack/{base}"]

def build_defense_url(name: str) -> List[str]:
    base = name.replace(" ", "_")
    return [f"{BASE_URL}Defense/{base}"]

def build_utility_url(name: str) -> List[str]:
    base = name.replace(" ", "_")
    return [f"{BASE_URL}Utility/{base}"]

@dataclass
class EnhancementData:
    name: str
    category: str  # attack/defense/utility
    url: Optional[str]
    description: str
    sample_rows: List[Dict]
    value_start: Optional[float] = None
    value_increment: Optional[float] = None
    max_level: Optional[int] = None
    formula: Optional[str] = None
    interpolated_levels: Optional[List[Dict]] = None
    status: str = "scraped"

INCREMENT_RE = re.compile(r"increases by ([0-9]+\.?[0-9]*)x per level", re.IGNORECASE)
START_RE = re.compile(r"starts at ([0-9]+\.?[0-9]*)x", re.IGNORECASE)
MAX_RE = re.compile(r"max(?:imum)? of ([0-9]+) levels", re.IGNORECASE)

VALUE_CELL_RE = re.compile(r"([0-9]+\.?[0-9]*)x")
COIN_CELL_RE = re.compile(r"[0-9,.]+[A-Z]?")  # e.g. 5.00B, 55.54B


def fetch(url: str) -> Optional[str]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=25)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None


def parse_page(html: str) -> tuple[str, List[Dict]]:
    """Extract description paragraph and sample table rows."""
    soup = BeautifulSoup(html, "html.parser")
    # Description: first <p> following the main heading containing the enhancement name.
    description = ""
    # Take first paragraph that looks like descriptive (contains 'Starts' or 'increase' or 'level').
    for p in soup.find_all('p'):
        t = p.get_text(strip=True)
        if any(kw in t.lower() for kw in ['start', 'increase', 'level', 'unlocked']):
            description = t
            break
    # Table rows
    sample_rows: List[Dict] = []
    tables = soup.find_all('table')
    for table in tables:
        headers = [th.get_text(strip=True) for th in table.find_all('th')]
        if not headers:
            continue
        if {'Level', 'Value', 'Coins'}.issubset(set(h.title() for h in headers)):  # loose check
            for tr in table.find_all('tr')[1:]:  # skip header
                tds = tr.find_all('td')
                if len(tds) < 3:
                    continue
                level_txt = tds[0].get_text(strip=True)
                value_txt = tds[1].get_text(strip=True)
                coins_txt = tds[2].get_text(strip=True)
                total_txt = tds[3].get_text(strip=True) if len(tds) > 3 else ''
                try:
                    level = int(re.findall(r"[0-9]+", level_txt)[0])
                except Exception:
                    continue
                sample_rows.append({
                    'level': level,
                    'value_raw': value_txt,
                    'coins_raw': coins_txt,
                    'total_coins_raw': total_txt
                })
            break  # first matching table only
    return description, sample_rows


def infer_formula(description: str) -> tuple[Optional[float], Optional[float], Optional[int], Optional[str]]:
    if not description:
        return None, None, None, None
    start_match = START_RE.search(description)
    inc_match = INCREMENT_RE.search(description)
    max_match = MAX_RE.search(description)
    value_start = float(start_match.group(1)) if start_match else None
    inc = float(inc_match.group(1)) if inc_match else None
    max_level = int(max_match.group(1)) if max_match else None
    formula = None
    if value_start is not None and inc is not None:
        # If description says starts at 1x and increases by 0.01x per level, often level 0 is 1.00x, level 1 is 1.01x.
        # We will treat shown sequence using value = value_start + inc * level.
        formula = f"value(level) = {value_start:.2f} + {inc:.4f} * level"
    return value_start, inc, max_level, formula


def build_value_interpolation(data: EnhancementData) -> None:
    """Populate interpolated_levels with predicted values for all levels up to max_level.

    Strategy:
    1. Prefer explicit formula from description (value_start + inc * level).
    2. If missing, attempt to derive constant per-level increment from sample_rows.
    3. Fall back to None if insufficient information.
    Formatting uses two decimals then 'x'.
    """
    if not data.max_level:
        return
    # Attempt direct formula
    increment = data.value_increment
    start = data.value_start
    if increment is None or start is None:
        # Derive from sample rows
        levels = sorted(r['level'] for r in data.sample_rows)
        values = []
        for r in data.sample_rows:
            m = re.match(r"([0-9]+\.?[0-9]*)x", r['value_raw'])
            if m:
                values.append(float(m.group(1)))
            else:
                values.append(None)
        deltas = []
        last_val = None
        last_level = None
        for lvl, val in zip(levels, values):
            if last_val is not None and val is not None:
                dl = lvl - last_level
                if dl > 0:
                    deltas.append((val - last_val) / dl)
            last_val = val
            last_level = lvl
        if deltas:
            # Test if deltas are near constant
            avg = sum(d for d in deltas if d is not None) / len(deltas)
            if all(abs(d - avg) < 1e-6 for d in deltas):
                increment = avg
                start = values[0] - increment * levels[0]  # solve for start based on first sample
    if increment is None or start is None:
        return
    interpolated = []
    sample_map = {r['level']: r for r in data.sample_rows}
    for lvl in range(1, data.max_level + 1):
        predicted_val = start + increment * lvl
        interpolated.append({
            'level': lvl,
            'value': round(predicted_val, 4),
            'value_formatted': f"{predicted_val:.2f}x",
            'sample': lvl in sample_map,
        })
    data.interpolated_levels = interpolated


def discover_enhancement_links() -> Dict[str, List[tuple[str,str]]]:
    """Attempt to discover enhancement links dynamically from the main Workshop Enhancement page."""
    page_url = "https://the-tower-idle-tower-defense.fandom.com/wiki/Workshop_Enhancement"
    print(f"Discovering enhancement links from {page_url}...")
    html = fetch(page_url)
    if not html:
        print("  ✗ Failed to fetch main page")
        return {}
    soup = BeautifulSoup(html, "html.parser")
    categories = {"attack": [], "defense": [], "utility": []}
    for a in soup.find_all('a'):
        href = a.get('href') or ''
        text = a.get_text(strip=True)
        if not href or not text:
            continue
        lower = href.lower()
        if "/workshop_enhancement/attack/" in lower:
            categories['attack'].append((text, href))
        elif "/workshop_enhancement/defense/" in lower:
            categories['defense'].append((text, href))
        elif "/workshop_enhancement/utility/" in lower:
            categories['utility'].append((text, href))
    # Deduplicate preserving order
    for cat, items in categories.items():
        seen = set()
        dedup = []
        for name, url in items:
            if name not in seen:
                seen.add(name)
                # Ensure absolute URL
                if url.startswith('/'):
                    url = 'https://the-tower-idle-tower-defense.fandom.com' + url
                dedup.append((name, url))
        categories[cat] = dedup
        print(f"  Found {len(dedup)} {cat} enhancements")
    return categories


def scrape_category(name_list: List[str], category: str, url_builder) -> List[EnhancementData]:
    results: List[EnhancementData] = []
    for enh in name_list:
        urls = url_builder(enh)
        page_html = None
        chosen_url = None
        for u in urls:
            page_html = fetch(u)
            if page_html:
                chosen_url = u
                break
        if not page_html:
            continue
        desc, rows = parse_page(page_html)
        v_start, inc, max_level, formula = infer_formula(desc)
        results.append(EnhancementData(
            name=enh,
            category=category,
            url=chosen_url,
            description=desc,
            sample_rows=rows,
            value_start=v_start,
            value_increment=inc,
            max_level=max_level,
            formula=formula
        ))
        time.sleep(1.2)  # polite delay
    return results


def build_payload(data: List[EnhancementData]) -> Dict:
    return {
        'meta': {
            'retrieved_at': datetime.now(timezone.utc).isoformat(),
            'source_base': BASE_URL,
            'count': len(data),
            'categories': sorted(set(d.category for d in data))
        },
        'enhancements': [asdict(d) for d in data]
    }


def main():
    parser = argparse.ArgumentParser(description='Scrape Workshop Enhancement detail pages.')
    parser.add_argument('--out', default='assets/workshop_enhancements.json', help='Output JSON path.')
    parser.add_argument('--limit', choices=['attack','defense','utility','all'], default='all', help='Restrict scrape.')
    parser.add_argument('--interpolate', action='store_true', help='Generate full value interpolation up to max level.')
    parser.add_argument('--discover', action='store_true', help='Discover enhancement links dynamically instead of static lists.')
    args = parser.parse_args()

    targets: List[EnhancementData] = []
    if args.discover:
        print("Using dynamic discovery mode...")
        discovered = discover_enhancement_links()
        def fetch_direct(entries: List[tuple[str,str]], cat: str):
            out = []
            for name, url in entries:
                print(f"  Fetching {cat}/{name}...")
                html = fetch(url)
                if not html:
                    print(f"    ✗ Failed to fetch")
                    continue
                desc, rows = parse_page(html)
                v_start, inc, max_level, formula = infer_formula(desc)
                print(f"    ✓ {len(rows)} samples, max_level={max_level}")
                ed = EnhancementData(name=name, category=cat, url=url, description=desc, sample_rows=rows,
                                     value_start=v_start, value_increment=inc, max_level=max_level, formula=formula)
                out.append(ed)
                time.sleep(1.0)
            return out
        if args.limit in ('attack','all') and discovered.get('attack'):
            print(f"\nScraping {len(discovered['attack'])} attack enhancements...")
            targets += fetch_direct(discovered['attack'], 'attack')
        if args.limit in ('defense','all') and discovered.get('defense'):
            print(f"\nScraping {len(discovered['defense'])} defense enhancements...")
            targets += fetch_direct(discovered['defense'], 'defense')
        if args.limit in ('utility','all') and discovered.get('utility'):
            print(f"\nScraping {len(discovered['utility'])} utility enhancements...")
            targets += fetch_direct(discovered['utility'], 'utility')
    else:
        print("Using static lists mode...")
        if args.limit in ('attack','all'):
            targets += scrape_category(ATTACK_ENHANCEMENTS, 'attack', build_attack_url)
        if args.limit in ('defense','all'):
            targets += scrape_category(DEFENSE_ENHANCEMENTS, 'defense', build_defense_url)
        if args.limit in ('utility','all'):
            targets += scrape_category(UTILITY_ENHANCEMENTS, 'utility', build_utility_url)

    if args.interpolate:
        print(f"\nGenerating interpolations for {len(targets)} enhancements...")
        for t in targets:
            build_value_interpolation(t)
            if t.interpolated_levels:
                print(f"  ✓ {t.name}: {len(t.interpolated_levels)} levels")
            else:
                print(f"  ✗ {t.name}: interpolation failed")

    payload = build_payload(targets)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {out_path} with {payload['meta']['count']} enhancements.")

if __name__ == '__main__':
    main()
