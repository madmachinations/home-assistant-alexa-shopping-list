#!/usr/bin/env python3

"""Base shopping list provider interface."""

from abc import ABC, abstractmethod
from typing import List
import hashlib
import json


class ShoppingListProvider(ABC):
    """Abstract base class for shopping list providers."""

    def __init__(self, hass):
        """Initialize the provider.
        
        Args:
            hass: Home Assistant instance
        """
        self.hass = hass

    @abstractmethod
    async def read_list(self) -> List[dict]:
        """Read the current shopping list.
        
        Returns:
            List of items with format: [{"name": str, "complete": bool}, ...]
        """
        pass

    @abstractmethod
    async def export_list(self, items: List[str]) -> None:
        """Export/sync the shopping list with given items.
        
        Args:
            items: List of item names to sync to the shopping list
        """
        pass

    async def get_list_hash(self) -> str:
        """Get hash of current shopping list for change detection.
        
        Returns:
            MD5 hash of the serialized shopping list
        """
        current_list = await self.read_list()
        serialized = json.dumps(current_list, sort_keys=True)
        return hashlib.md5(serialized.encode('utf-8')).hexdigest()

    @abstractmethod
    async def refresh(self) -> None:
        """Refresh the shopping list in Home Assistant if needed."""
        pass
