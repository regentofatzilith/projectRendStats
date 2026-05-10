"""Merge manual lab overrides (e.g. missing early Critical Factor levels) into existing lab upgrades JSON.

Usage (PowerShell):
        python merge_lab_overrides.py --base assets/lab_upgrades_tables.json --overrides assets/lab_manual_overrides.json --out assets/lab_upgrades_tables.json

Extended Behavior:
    - Matches items by slug (preferred) then by name.
    - For each override level: if level exists, replaced; else inserted.
    - If the override item includes "replace_all": true then the target levels are fully replaced.
    - Heuristic auto-replacement: if target.max_level <= 99 AND all existing levels >= 100 AND override provides any level < 100, treat existing set as a mis-scrape (workshop bleed-through) and replace.
    - Levels list sorted ascending by level after merge / replacement.
    - Adds an "override_applied": true flag and optionally "override_mode": "replace" | "merge" to the item for downstream transparency.
    - Preserves existing item metadata & errors list unless replaced.
    - Recomputes meta.errors_count after merge.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Dict, Any


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text())


def should_replace_all(base_item: dict, override_item: dict) -> bool:
    """Decide whether to fully replace the level list.

    Replacement triggers:
      1. Explicit override flag replace_all: true
      2. Heuristic: base max_level <= 99, all base levels >= 100, and override has any level < 100.
    """
    if override_item.get('replace_all'):
        return True
    base_levels = base_item.get('levels', [])
    if not base_levels:
        return False  # nothing to replace; will just merge
    base_lv_nums = [lvl.get('level') for lvl in base_levels if isinstance(lvl.get('level'), int)]
    if not base_lv_nums:
        return False
    override_lv_nums = [lvl.get('level') for lvl in override_item.get('levels', [])]
    max_lv = base_item.get('max_level')
    if (isinstance(max_lv, int) and max_lv <= 99 and
        all(lv >= 100 for lv in base_lv_nums) and any(isinstance(lv, int) and lv < 100 for lv in override_lv_nums)):
        return True
    return False


def merge_item(base_item: dict, override_item: dict) -> dict:
    if should_replace_all(base_item, override_item):
        base_item['levels'] = override_item.get('levels', [])
        base_item['override_applied'] = True
        base_item['override_mode'] = 'replace'
        return base_item
    # Merge mode
    base_levels_map = {lvl['level']: lvl for lvl in base_item.get('levels', [])}
    for ov in override_item.get('levels', []):
        base_levels_map[ov['level']] = ov  # replace or insert
    merged_levels = [base_levels_map[k] for k in sorted(base_levels_map)]
    base_item['levels'] = merged_levels
    base_item['override_applied'] = True
    base_item['override_mode'] = 'merge'
    return base_item


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='assets/lab_upgrades_tables.json')
    ap.add_argument('--overrides', default='assets/lab_manual_overrides.json')
    ap.add_argument('--out', default='assets/lab_upgrades_tables.json')
    args = ap.parse_args()

    base_path = Path(args.base)
    over_path = Path(args.overrides)
    out_path = Path(args.out)

    base = load_json(base_path)
    overrides = load_json(over_path)

    # Build index of base items by slug & name
    by_slug = {it['slug']: it for it in base['items']}
    by_name = {it['name']: it for it in base['items']}

    for ov in overrides.get('items', []):
        target = by_slug.get(ov.get('slug')) or by_name.get(ov.get('name'))
        if not target:
            print(f"[WARN] Override item not found in base: {ov.get('name')} ({ov.get('slug')})")
            continue
        before_cnt = len(target.get('levels', []))
        merge_item(target, ov)
        after_cnt = len(target.get('levels', []))
        print(f"Applied overrides for {target['name']} mode={target.get('override_mode')} levels {before_cnt} -> {after_cnt}")

    # Recompute meta errors_count (unchanged here) and write
    base['meta']['errors_count'] = sum(1 for it in base['items'] if it.get('errors'))
    out_path.write_text(json.dumps(base, indent=2))
    print(f"Wrote merged lab JSON to {out_path}")


if __name__ == '__main__':
    main()
