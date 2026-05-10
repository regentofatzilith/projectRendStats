"""Generate concise manifest of active (non-archived) project files.

Scans the workspace root recursively, excluding:
  - _archive/*
  - __pycache__ directories

Produces assets/active_manifest.json with high-level grouping.

Usage:
    python generate_active_manifest.py
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List

ROOT = Path('.')
OUT = Path('assets/active_manifest.json')
EXCLUDE_DIRS = {'_archive', '__pycache__'}


def gather_files() -> List[Path]:
    files: List[Path] = []
    for p in ROOT.rglob('*'):
        if p.is_dir():
            if p.name in EXCLUDE_DIRS:
                continue
            # skip any path containing _archive segment
            if any(seg == '_archive' for seg in p.parts):
                continue
            continue  # only collecting files
        if any(seg == '_archive' for seg in p.parts):
            continue
        if '__pycache__' in p.parts:
            continue
        files.append(p)
    return files


def classify(files: List[Path]) -> Dict[str, List[str]]:
    groups: Dict[str, List[str]] = {
        'python_scripts': [],
        'assets_json': [],
        'data_files': [],
        'other': []
    }
    for f in files:
        rel = f.as_posix()
        if rel.startswith('assets/') and f.suffix == '.json':
            groups['assets_json'].append(rel)
        elif f.suffix == '.py':
            groups['python_scripts'].append(rel)
        elif f.parent.name == 'analysis':
            groups['data_files'].append(rel)
        else:
            groups['other'].append(rel)
    for k in groups:
        groups[k].sort()
    return groups


def main():
    files = gather_files()
    groups = classify(files)
    manifest = {
        'meta': {
            'file_count': sum(len(v) for v in groups.values()),
        },
        'groups': groups
    }
    OUT.write_text(json.dumps(manifest, indent=2))
    print(f"Wrote manifest with {manifest['meta']['file_count']} files to {OUT}")


if __name__ == '__main__':
    main()
