"""
Test script to print Chrono Field ultimate weapon data from the datastore.
Displays levels and effective values from relics, labs, and ultimate weapons.
"""
import json
from pathlib import Path
from functions.data.DataStore import UserDataStore

def print_chrono_field_data():
    # Initialize the data store
    datastore = UserDataStore()
    
    # Try to find and load a JSON file (typical location)
    json_path = Path(r"C:\\Users\\thors\\AppData\\Roaming\\rendapp\\userData.json")
    
    if not json_path.exists():
        print(f"❌ Could not find JSON file at: {json_path}")
        print("\nPlease provide the correct path to your game data JSON file.")
        return
    
    print(f"📂 Loading data from: {json_path}")
    
    # Load the JSON into datastore
    with open(json_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    datastore.full_json = json_data
    
    print("\n" + "="*80)
    print("CHRONO FIELD - Ultimate Weapon Data")
    print("="*80)
    
    # Get combined weapons data
    try:
        combined_data = datastore.get_combined_weapons_data(selected_module="Primordial Collapse")
        
        if "Chrono Field" in combined_data:
            chrono_df = combined_data["Chrono Field"]
            
            if not chrono_df.empty:
                print(f"\n📊 Chrono Field Data ({len(chrono_df)} parameters):")
                print("-" * 80)
                
                # Display the data in a nice format
                for idx, row in chrono_df.iterrows():
                    param = row.get('Parameter', 'Unknown')
                    level = row.get('Level', 0)
                    target = row.get('Target Level', 0)
                    module_effect = row.get('Module Effect', 0)
                    labs_level = row.get('Labs Level', 0)
                    total_value = row.get('Total Value', 0)
                    
                    print(f"\n🔹 {param}:")
                    print(f"   Ultimate Weapon Level: {level}/{target}")
                    print(f"   Labs Research Level: {labs_level}")
                    print(f"   Module Effect: {module_effect}")
                    print(f"   💎 Total Effective Value: {total_value}")
                
                # Also show the raw dataframe
                print("\n" + "="*80)
                print("📋 Full DataFrame:")
                print("="*80)
                print(chrono_df.to_string(index=False))
            else:
                print("❌ Chrono Field DataFrame is empty!")
        else:
            print("❌ Chrono Field not found in combined data!")
            print(f"\nAvailable weapons: {list(combined_data.keys())}")
    except Exception as e:
        print(f"\n❌ Error extracting combined weapons data: {e}")
        import traceback
        traceback.print_exc()
    
    # Also try the detailed levels and values method
    print("\n" + "="*80)
    print("DETAILED LEVELS AND VALUES")
    print("="*80)
    
    try:
        detailed_data = datastore.get_current_weapon_levels_and_values(selected_module="Primordial Collapse")
        
        if "Chrono Field" in detailed_data:
            chrono_details = detailed_data["Chrono Field"]
            header = detailed_data.get("header", [])
            
            print(f"\n📊 Chrono Field Detailed Breakdown:")
            print("-" * 80)
            print(f"\nHeader: {header}")
            
            for param, values in chrono_details.items():
                print(f"\n🔹 {param}:")
                if header:
                    for i, field_name in enumerate(header):
                        if i < len(values):
                            print(f"   {field_name}: {values[i]}")
                else:
                    print(f"   Values: {values}")
        else:
            print("❌ Chrono Field not found in detailed data!")
            print(f"\nAvailable weapons: {[k for k in detailed_data.keys() if k != 'header']}")
    except Exception as e:
        print(f"\n❌ Error extracting detailed levels and values: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Chrono Field Data Extraction...")
    print_chrono_field_data()
    print("\n✅ Done!")
