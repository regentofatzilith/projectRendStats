from functions.data import UserDataStore
#from myproject.DataStore import parse_user_dataframes

# Example usage:
store = UserDataStore.get()
store.load_from_path("C:\\Users\\thors\\AppData\\Roaming\\rendapp\\userData.json")
uw_data = store.get_current_weapon_levels_and_values(selected_module="Primordial Collapse")
header = uw_data.get("header", [])
weapon = "Death Wave"
print(f"Header: {header}")
if weapon in uw_data:
    print(f"\n{weapon}:")
    for param, values in uw_data[weapon].items():
        print(f"  {param}: {values}")
else:
    print(f"No data found for '{weapon}'. Available weapons: {', '.join([k for k in uw_data.keys() if k != 'header'])}")