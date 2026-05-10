"""Quick test of the scraper to verify it works."""
import sys
sys.path.insert(0, '.')

from scrape_workshop_enhancements import (
    fetch, parse_page, infer_formula, build_value_interpolation,
    EnhancementData
)

# Test fetching damage page
url = "https://the-tower-idle-tower-defense.fandom.com/wiki/Workshop_Enhancement/Attack/Damage"
print(f"Fetching {url}...")
html = fetch(url)

if html:
    print(f"✓ Fetched {len(html)} bytes")
    desc, rows = parse_page(html)
    print(f"✓ Description: {desc[:100]}...")
    print(f"✓ Sample rows: {len(rows)}")
    
    v_start, inc, max_level, formula = infer_formula(desc)
    print(f"✓ Inferred: start={v_start}, inc={inc}, max={max_level}")
    print(f"✓ Formula: {formula}")
    
    # Test interpolation
    data = EnhancementData(
        name="Damage",
        category="attack",
        url=url,
        description=desc,
        sample_rows=rows,
        value_start=v_start,
        value_increment=inc,
        max_level=max_level,
        formula=formula
    )
    build_value_interpolation(data)
    
    if data.interpolated_levels:
        print(f"✓ Interpolated {len(data.interpolated_levels)} levels")
        print(f"  Level 1: {data.interpolated_levels[0]}")
        print(f"  Level 10: {data.interpolated_levels[9]}")
        print(f"  Level 400: {data.interpolated_levels[399]}")
    else:
        print("✗ Interpolation failed")
else:
    print("✗ Failed to fetch page")
