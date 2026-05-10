"""Functions package - main business logic modules."""

from .data.DataStore import UserDataStore

# Convenience alias
user_data_store = UserDataStore.get()

__all__ = ["UserDataStore", "user_data_store"]
