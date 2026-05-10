"""Test script to validate workshop and labs todo extraction."""
import os
from pathlib import Path
from functions.data import load_todos_and_costs

# Find userData.json (same logic as app.py)
candidates = [
    Path(r'C:\Users\thors\AppData\Roaming\rendapp\userData.json'),
    Path.home() / 'AppData' / 'Roaming' / 'rendapp' / 'userData.json',
    Path(r'\\mycloudex2ultra\Thorsten\_python\ProjectAtzi\userData.json'),
]

path = None
for candidate in candidates:
    if candidate.exists():
        path = str(candidate)
        print(f"✓ Found JSON at: {path}")
        break

if not path:
    print("✗ No userData.json found in any candidate location.")
    print("Candidates checked:")
    for c in candidates:
        print(f"  - {c}")
    exit(1)

# Load todos
print("\n" + "="*60)
print("Loading todos and costs...")
print("="*60)

results = load_todos_and_costs(path)

# Display workshop todos
print("\n📋 WORKSHOP TODOS:")
print("-" * 60)
workshop_todos = results['workshop_todos_df']
if workshop_todos.empty:
    print("(No workshop todos found)")
else:
    print(f"Found {len(workshop_todos)} workshop upgrade todos:\n")
    # Group by category for better readability
    for category in workshop_todos['category'].unique():
        cat_items = workshop_todos[workshop_todos['category'] == category]
        print(f"\n  {category.upper()} ({len(cat_items)} items):")
        for _, row in cat_items.head(5).iterrows():
            print(f"    • {row['name']:30s} Lvl {row['level'] or 0:2d} → {row['targetLevel']:2d} ({row['remaining_levels']} levels)")
        if len(cat_items) > 5:
            print(f"    ... and {len(cat_items) - 5} more")

# Display labs todos
print("\n🧪 LABS TODOS:")
print("-" * 60)
labs_todos = results['labs_todos_df']
if labs_todos.empty:
    print("(No labs todos found)")
else:
    print(f"Found {len(labs_todos)} lab upgrade todos:\n")
    for _, row in labs_todos.head(10).iterrows():
        print(f"  • Lab {row['lab_id']:>3s}: {row['name']:30s} Lvl {row['level'] or 0:2d} → {row['targetLevel']:2d} ({row['remaining_levels']} levels)")
    if len(labs_todos) > 10:
        print(f"  ... and {len(labs_todos) - 10} more")

# Summary statistics
print("\n📊 SUMMARY:")
print("-" * 60)
workshop_all = results['workshop_all_df']
labs_all = results['labs_all_df']

if not workshop_all.empty:
    total_workshop = len(workshop_all)
    todo_workshop = len(workshop_todos)
    print(f"Workshop: {todo_workshop}/{total_workshop} items need upgrades ({todo_workshop/total_workshop*100:.1f}%)")
    if todo_workshop > 0:
        total_remaining = workshop_todos['remaining_levels'].sum()
        print(f"          Total {total_remaining} levels to upgrade")

if not labs_all.empty:
    total_labs = len(labs_all)
    todo_labs = len(labs_todos)
    print(f"Labs:     {todo_labs}/{total_labs} items need upgrades ({todo_labs/total_labs*100:.1f}%)")
    if todo_labs > 0:
        total_remaining = labs_todos['remaining_levels'].sum()
        print(f"          Total {total_remaining} levels to upgrade")

print("\n✓ Extraction test complete!")
