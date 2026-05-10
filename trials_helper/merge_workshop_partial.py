"""Merge partial workshop upgrade scrape results into existing full JSON.

Usage (PowerShell):
    python merge_workshop_partial.py --base assets/workshop_upgrades_tables.json --partial assets/workshop_upgrades_partial.json --out assets/workshop_upgrades_tables.json

Will replace items (by exact name match) found in the partial file inside the base file, update meta.retrieved_at and errors_count.
"""
from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def load(path: str):
    return json.loads(Path(path).read_text())


def main():
    p = argparse.ArgumentParser(description="Merge partial workshop upgrade items into existing JSON")
    p.add_argument("--base", required=True, help="Path to existing full JSON")
    p.add_argument("--partial", required=True, help="Path to partial JSON containing replacement items")
    p.add_argument("--out", required=True, help="Destination path for merged JSON (can overwrite base)")
    args = p.parse_args()

    base = load(args.base)
    part = load(args.partial)

    # Index partial items by name
    part_items = {it['name']: it for it in part['items']}

    replaced = 0
    for i, it in enumerate(base['items']):
        name = it['name']
        if name in part_items:
            base['items'][i] = part_items[name]
            replaced += 1

    # Update metadata
    base['meta']['retrieved_at'] = datetime.now(timezone.utc).isoformat()
    base['meta']['errors_count'] = sum(1 for it in base['items'] if it.get('errors'))

    Path(args.out).write_text(json.dumps(base, indent=2))
    print(f"Merged {replaced} items into {args.out}; errors_count={base['meta']['errors_count']}")


if __name__ == "__main__":
    main()
