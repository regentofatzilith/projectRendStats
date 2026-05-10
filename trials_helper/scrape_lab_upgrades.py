"""Scrape Lab Upgrade per-level tables (Level / Cost / Time / Value) from The Tower Idle wiki.

Workflow:
  1. Fetch main Lab Upgrades index page.
  2. Discover all lab item links & their max levels from collapsed category tables.
  3. For each lab page, parse the first table containing Level & Cost headers (and Time/Value if present).
  4. Normalize numeric fields (large-number suffixes, percents) and time strings to seconds.
  5. Emit structured JSON for downstream analysis.

Usage (PowerShell):
    python scrape_lab_upgrades.py --out assets/lab_upgrades_tables.json
    python scrape_lab_upgrades.py --limit 5 --delay 0.5

License: Source content is CC-BY-SA via Fandom; this script extracts factual numeric data.
"""
from __future__ import annotations
import argparse
import json
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://the-tower-idle-tower-defense.fandom.com"
LAB_INDEX_URL = f"{BASE_URL}/wiki/Lab_Upgrades"
HEADERS = {"User-Agent": "ProjectAtziLabScraper/1.0 (+https://github.com/)"}

SUFFIX_MAP = {
    'K': 1e3, 'M': 1e6, 'B': 1e9, 'T': 1e12,
    'Qa': 1e15, 'Qi': 1e18, 'Sx': 1e21, 'Sp': 1e24,
    'Oc': 1e27, 'No': 1e30, 'Dc': 1e33
}
PERCENT_RE = re.compile(r"([0-9]*\.?[0-9]+)\s*%")
TIME_TOKEN_RE = re.compile(r"(\d+)\s*([dhms])", re.IGNORECASE)


@dataclass
class LabLevelRow:
    level: int
    cost_raw: str
    cost: Optional[float]
    time_raw: str
    time_seconds: Optional[int]
    value_raw: str
    value: Optional[float]
    total_cost_raw: Optional[str] = None
    total_cost: Optional[float] = None


@dataclass
class LabItem:
    name: str
    slug: str
    category: str
    url: str
    max_level: Optional[int]
    cost_unit: Optional[str]
    levels: List[LabLevelRow]
    errors: List[str]
    table_headers: List[str]
    notes: Optional[str] = None  # optional free-form context when table missing or additional bullet labs detected


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
    pm = PERCENT_RE.search(t)
    if pm:
        try:
            return float(pm.group(1)) / 100.0
        except ValueError:
            pass
    # Handle multiplier formats like x2.0 or 1.30x or x3 (strip leading/trailing 'x')
    mx = re.match(r"x?([0-9]*\.?[0-9]+)x?$", t, re.IGNORECASE)
    if mx and 'q' not in t.lower():  # avoid conflict with quadrillion suffix
        try:
            return float(mx.group(1))
        except ValueError:
            pass
    t = t.replace(',', '').replace(' ', '')
    try:
        return float(t)
    except ValueError:
        pass
    m = re.match(r"([0-9]*\.?[0-9]+)([A-Za-z]+)$", t)
    if m:
        base, suffix = m.groups()
        # Support single-letter q/Q for quadrillion
        if suffix in {'q', 'Q'}:
            mult = 1e15
        else:
            mult = SUFFIX_MAP.get(suffix)
        if mult:
            try:
                return float(base) * mult
            except ValueError:
                return None
    return None


def parse_time(text: str) -> Optional[int]:
    if not text:
        return None
    total = 0
    for num, unit in TIME_TOKEN_RE.findall(text.lower()):
        v = int(num)
        if unit == 'd':
            total += v * 86400
        elif unit == 'h':
            total += v * 3600
        elif unit == 'm':
            total += v * 60
        elif unit == 's':
            total += v
    return total or None


def discover_labs(index_html: str) -> Dict[str, List[Tuple[str, str, Optional[int]]]]:
    soup = BeautifulSoup(index_html, 'html.parser')
    categories: Dict[str, List[Tuple[str, str, Optional[int]]]] = {}
    for table in soup.find_all('table', class_='mw-collapsible'):
        # First <th> contains category name after the button span
        th = table.find('th')
        if not th:
            continue
        cat_text = th.get_text(separator=' ', strip=True)
        # Remove 'Expand' word
        cat = cat_text.replace('Expand', '').strip()
        if not cat:
            continue
        items: List[Tuple[str, str, Optional[int]]] = []
        for a in table.find_all('a'):
            name = a.get_text(strip=True)
            href_attr = a.get('href')
            href = str(href_attr) if href_attr else None
            if not name or not href:
                continue
            # Extract max level if present in sibling <div>
            parent_td = a.find_parent('td')
            max_level = None
            if parent_td:
                div = parent_td.find('div')
                if div:
                    m = re.search(r"Max\s*Lv\s*(\d+)", div.get_text())
                    if m:
                        max_level = int(m.group(1))
            url = href if href.startswith('http') else f"{BASE_URL}{href}"
            items.append((name, url, max_level))
        if items:
            categories[cat] = items
    return categories


def locate_lab_table(soup: BeautifulSoup):  # return Tag or None
    # Look for table headers containing Level/Slot and Cost/Coins/Gem Cost
    for table in soup.find_all('table'):
        headers = [th.get_text(strip=True).lower() for th in table.find_all('th')]
        has_level = any('level' in h or 'slot' in h for h in headers)
        has_cost = any('cost' in h or 'coins' in h or 'gem' in h for h in headers)
        if has_level and has_cost:
            return table
    return None


def find_table_near_heading(soup: BeautifulSoup, name: str, url: str):
    # Try fragment anchor first
    if '#' in url:
        frag = url.split('#', 1)[1]
        anchor = soup.find(id=frag)
        if anchor:
            nxt = anchor
            for _ in range(50):
                nxt = nxt.find_next()
                if not nxt:
                    break
                if nxt.name == 'table':
                    return nxt
    # Try matching by heading text
    target = name.lower()
    for tag in soup.find_all(['h1','h2','h3','h4','span']):
        text = tag.get_text(strip=True).lower()
        if target in text:
            nxt = tag
            for _ in range(50):
                nxt = nxt.find_next()
                if not nxt:
                    break
                if nxt.name == 'table':
                    return nxt
    return None

def parse_lab_table(html: str, name: str, category: str, url: str, max_level: Optional[int]) -> LabItem:
    soup = BeautifulSoup(html, 'html.parser')
    table = find_table_near_heading(soup, name, url) or locate_lab_table(soup)
    # Special-case: Critical Factor page has multiple tables; prefer the one whose value cells contain multiplier 'x'
    if name.lower() == 'critical factor':
        candidate_tables = []
        for tbl in soup.find_all('table'):
            headers = [th.get_text(strip=True).lower() for th in tbl.find_all('th')]
            if any('level' in h for h in headers) and any('value' in h for h in headers):
                # inspect cells for multiplier pattern
                text_cells = ' '.join(td.get_text(strip=True).lower() for td in tbl.find_all('td'))
                if re.search(r"\bx[0-9]+(\.[0-9]+)?\b|\b[0-9]+(\.[0-9]+)?x\b", text_cells):
                    candidate_tables.append(tbl)
        if candidate_tables:
            # choose the first candidate containing multipliers; overrides default selection
            table = candidate_tables[0]
    levels: List[LabLevelRow] = []
    errors: List[str] = []
    headers_lower: List[str] = []
    cost_unit: Optional[str] = None
    notes: Optional[str] = None
    if not table:
        errors.append('No suitable table found')
        # Attempt to extract bullet-like sub-lab names (lines starting with a bullet • ) for additional context
        bullets: List[str] = []
        # Collect text from paragraphs and headings to search for bullet glyphs
        for tag in soup.find_all(['p','div','span']):
            txt = tag.get_text('\n', strip=True)
            if '•' in txt:
                for line in txt.split('\n'):
                    line = line.strip()
                    if line.startswith('•'):
                        # remove leading bullet and trailing punctuation
                        cleaned = line.lstrip('•').strip().rstrip('.')
                        if cleaned:
                            bullets.append(cleaned)
        if bullets:
            notes = f"Detected bullet entries: {', '.join(bullets)}"
        return LabItem(name=name, slug=slugify(name), category=category, url=url, max_level=max_level, cost_unit=cost_unit, levels=levels, errors=errors, table_headers=headers_lower, notes=notes)
    headers = [th.get_text(strip=True) for th in table.find_all('th')]
    headers_lower = [h.lower() for h in headers]

    def idx_any(keys: List[str]) -> Optional[int]:
        for key in keys:
            for i, h in enumerate(headers_lower):
                if key == h:
                    return i
            for i, h in enumerate(headers_lower):
                if key in h:
                    return i
        return None

    level_idx = idx_any(['level', 'slot'])
    cost_idx = idx_any(['cost', 'coins', 'gem cost'])
    if cost_idx is not None:
        ht = headers_lower[cost_idx]
        if 'gem' in ht:
            cost_unit = 'gems'
        elif 'q coins' in ht or '(q' in ht or ht.endswith(' q'):
            cost_unit = 'Q'
    time_idx = idx_any(['time'])
    value_idx = idx_any(['value'])

    for r in table.find_all('tr')[1:]:
        cells = r.find_all(['td','th'])
        if not cells or level_idx is None or cost_idx is None:
            continue
        lv_raw = cells[level_idx].get_text(strip=True)
        try:
            lv = int(re.sub(r"[^0-9]", "", lv_raw))
        except ValueError:
            continue
        cost_raw = cells[cost_idx].get_text(strip=True)
        time_raw = cells[time_idx].get_text(strip=True) if time_idx is not None and time_idx < len(cells) else ''
        value_raw = cells[value_idx].get_text(strip=True) if value_idx is not None and value_idx < len(cells) else ''
        levels.append(LabLevelRow(
            level=lv,
            cost_raw=cost_raw,
            cost=parse_number(cost_raw),
            time_raw=time_raw,
            time_seconds=parse_time(time_raw) if time_raw else None,
            value_raw=value_raw,
            value=parse_number(value_raw)
        ))
    if not levels:
        errors.append('Parsed 0 level rows')
    return LabItem(name=name, slug=slugify(name), category=category, url=url, max_level=max_level, cost_unit=cost_unit, levels=levels, errors=errors, table_headers=headers_lower, notes=notes)


def build_payload(categories: Dict[str, List[Tuple[str, str, Optional[int]]]], items: List[LabItem]) -> Dict:
    return {
        'meta': {
            'source_index_url': LAB_INDEX_URL,
            'retrieved_at': datetime.now(timezone.utc).isoformat(),
            'category_count': len(categories),
            'item_count': len(items),
            'errors_count': sum(1 for i in items if i.errors),
            'license': 'CC-BY-SA (Fandom) - numeric factual data only'
        },
        'categories': {
            cat: [
                {'name': name, 'url': url, 'max_level': max_level}
                for name, url, max_level in entries
            ] for cat, entries in categories.items()
        },
        'items': [
            {
                **{k: v for k, v in asdict(it).items() if k != 'levels'},
                'levels': [asdict(lr) for lr in it.levels]
            } for it in items
        ]
    }


def main():
    parser = argparse.ArgumentParser(description='Scrape lab upgrade tables.')
    parser.add_argument('--out', type=str, default='assets/lab_upgrades_tables.json', help='Output JSON path')
    parser.add_argument('--limit', type=int, default=None, help='Optional limit of items for testing')
    parser.add_argument('--delay', type=float, default=0.75, help='Delay seconds between requests')
    args = parser.parse_args()

    index_html = fetch(LAB_INDEX_URL)
    categories = discover_labs(index_html)
    all_entries: List[Tuple[str,str,str,Optional[int]]] = []  # (category,name,url,max_level)
    for cat, entries in categories.items():
        for name, url, max_level in entries:
            all_entries.append((cat, name, url, max_level))
    if args.limit:
        all_entries = all_entries[:args.limit]

    items: List[LabItem] = []
    for i, (cat, name, url, max_level) in enumerate(all_entries, 1):
        try:
            html = fetch(url)
        except Exception as e:
            items.append(LabItem(name=name, slug=slugify(name), category=cat, url=url, max_level=max_level, cost_unit=None, levels=[], errors=[f'Fetch error: {e}'], table_headers=[]))
            continue
        item = parse_lab_table(html, name=name, category=cat, url=url, max_level=max_level)
        items.append(item)
        print(f"[{i}/{len(all_entries)}] {name}: rows={len(item.levels)} errors={'|'.join(item.errors) if item.errors else 'none'}")
        time.sleep(args.delay)

    payload = build_payload(categories, items)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {out_path} with {payload['meta']['item_count']} items; errors={payload['meta']['errors_count']}")


if __name__ == '__main__':
    main()
