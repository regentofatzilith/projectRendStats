"""Post-scrape data hygiene for lab & workshop datasets.

Generates:
  assets/lab_missing_tables_report.json        Summary of lab items with missing tables.
  assets/workshop_duplicates_report.json       Summary of potential duplicate / colliding workshop items by normalized slug.

Usage (PowerShell):
    python clean_lab_and_workshop.py

Non-destructive: does not modify original source JSONs.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List

LAB_JSON = Path("assets/lab_upgrades_tables.json")
WORKSHOP_JSON = Path("assets/workshop_upgrades_tables.json")
LAB_REPORT = Path("assets/lab_missing_tables_report.json")
WORKSHOP_REPORT = Path("assets/workshop_duplicates_report.json")


def load(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text())


def slugify(name: str) -> str:
    import re
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip('_')
    s = re.sub(r"_+", "_", s)
    return s


def lab_missing_tables(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    missing = []
    for it in data.get('items', []):
        if it.get('errors') and any('No suitable table found' in e for e in it.get('errors', [])):
            missing.append({
                'name': it.get('name'),
                'slug': it.get('slug'),
                'category': it.get('category'),
                'url': it.get('url'),
                'max_level': it.get('max_level'),
                'note_present': bool(it.get('notes')),  # future enrichment hook
            })
    return missing


def workshop_duplicates(data: Dict[str, Any]) -> Dict[str, Any]:
    # Build normalized slug groups
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for it in data.get('items', []):
        norm = slugify(it.get('name', ''))
        groups.setdefault(norm, []).append({'name': it.get('name'), 'slug': it.get('slug'), 'category': it.get('category')})
    duplicates = {slug: items for slug, items in groups.items() if len(items) > 1}
    return {
        'duplicate_slug_count': len(duplicates),
        'duplicates': duplicates,
        'colliding_slugs': sorted(duplicates.keys())
    }


def main():
    lab = load(LAB_JSON)
    ws = load(WORKSHOP_JSON)
    lab_report = {'meta': {'source': str(LAB_JSON), 'missing_count': lab['meta']['errors_count']}, 'missing_items': lab_missing_tables(lab)}
    ws_report = {'meta': {'source': str(WORKSHOP_JSON)}, **workshop_duplicates(ws)}
    LAB_REPORT.write_text(json.dumps(lab_report, indent=2))
    WORKSHOP_REPORT.write_text(json.dumps(ws_report, indent=2))
    print(f"Wrote {LAB_REPORT} (missing={lab_report['meta']['missing_count']})")
    print(f"Wrote {WORKSHOP_REPORT} (duplicate_slug_count={ws_report['duplicate_slug_count']})")


if __name__ == '__main__':
    main()
