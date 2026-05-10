#!/usr/bin/env bash
set -euo pipefail

# Build Linux distributable with PyInstaller.
# Run this on Linux (native host, VM, WSL2, Docker, CI runner).

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "[1/4] Installing dependencies"
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo "[2/4] Cleaning previous build output"
rm -rf build dist

echo "[3/4] Building Linux executable"
python3 -m PyInstaller build_linux.spec

echo "[4/4] Done"
echo "Binary directory: dist/TowerConquestAnalytics/"
echo "Run with: ./dist/TowerConquestAnalytics/TowerConquestAnalytics"
