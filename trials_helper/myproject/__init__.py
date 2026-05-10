"""Project package initialization.

Exports the singleton `UserDataStore` for convenience:

	from functions import user_data_store
	ds = user_data_store  # access methods like ds.load_from_path(...)

"""

from .DataStore import UserDataStore

# Convenience alias
user_data_store = UserDataStore.get()

__all__ = ["UserDataStore", "user_data_store"]
