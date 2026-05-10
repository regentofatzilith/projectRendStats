import pandas as pd
try:
    from .functions.data.ImportJSON import import_selected_sections
except ImportError:
    from functions.data.ImportJSON import import_selected_sections

#(path: str, card_id: int = 31) -> dict[str, pd.DataFrame]:
"""Import selected userData.json sections as DataFrames.

    Sections:
        1) cardTracker.cardSlots filtered by id
        2) gameStats (all runs)
        3) relicsData (all relics)
        4) workshopData (all workshops)
        5) modulesData (all modules, including submodules)
        6) labsProgress (all labs)
"""
df_labs = import_selected_sections("labsProgress").get("labsProgress", pd.DataFrame())
df_relics = import_selected_sections("relicsData").get("relicsData", pd.DataFrame())
df_workshops = import_selected_sections("workshopData").get("workshopData", pd.DataFrame())
df_modules = import_selected_sections("modulesData").get("modulesData", pd.DataFrame())


if __name__ == "__main__":    
    # Example usage: print the first few rows of each DataFrame
    print("Labs Progress:")
    print(df_labs.head())
    
    print("\nRelics Data:")
    print(df_relics.head())
    
    print("\nWorkshop Data:")
    print(df_workshops.head())
    
    print("\nModules Data:")
    print(df_modules.head())