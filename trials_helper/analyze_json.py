from pathlib import Path
from functions.data import analyze_full_json_file, save_json_analysis_to_assets
import os

# Discover userData.json using the same logic as app.py
PROJECT_ROOT = Path(__file__).resolve().parent
candidates = [
    PROJECT_ROOT / "assets" / "userData.json",
]
appdata = os.getenv("APPDATA")
if appdata:
    candidates.append(Path(appdata) / "rendapp" / "userData.json")
candidates.append(Path.home() / "AppData" / "Roaming" / "rendapp" / "userData.json")
candidates.append(Path(r"C:\\Users\\thors\\AppData\\Roaming\\rendapp\\userData.json"))

json_path = None
for p in candidates:
    if p.exists():
        json_path = p
        break

if not json_path:
    print("Could not find userData.json. Checked:")
    for p in candidates:
        print(" -", p)
    raise SystemExit(1)

print(f"Analyzing JSON at: {json_path}")
artifacts = save_json_analysis_to_assets(str(json_path))
print("Analysis complete. Artifacts written:")
for name, path in artifacts.items():
    print(f" - {name}: {path}")
