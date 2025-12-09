#!/usr/bin/env python3

"""Home Assistant default shopping list provider."""

import json
import os
import logging
from typing import List
from .base import ShoppingListProvider

_LOGGER = logging.getLogger(__name__)


class HAShoppingListProvider(ShoppingListProvider):
    """Provider for Home Assistant's default shopping list."""

    def __init__(self, hass, hasl_path: str, hasl_refresh):
        """Initialize the HA shopping list provider.
        
        Args:
            hass: Home Assistant instance
            hasl_path: Path to the .shopping_list.json file
            hasl_refresh: Callback to refresh the shopping list
        """
        super().__init__(hass)
        self._hasl_path = hasl_path
        self._hasl_refresh = hasl_refresh

    async def read_list(self) -> List[dict]:
        """Read the current HA shopping list.
        
        Returns:
            List of items with format: [{"name": str, "complete": bool, "id": str}, ...]
        """
        if os.path.exists(self._hasl_path):
            try:
                with open(self._hasl_path, 'r') as file:
                    return json.load(file)
            except (json.JSONDecodeError, IOError) as e:
                _LOGGER.error(f"Error reading HA shopping list from {self._hasl_path}: {e}")
                return []
        return []

    async def export_list(self, items: List[str]) -> None:
        """Export items to HA shopping list file.
        
        Args:
            items: List of item names to write to the shopping list
        """
        export = []
        for item in items:
            export.append({
                "id": item.replace(" ", "_"),
                "name": item,
                "complete": False
            })
        
        try:
            with open(self._hasl_path, "w") as outfile:
                outfile.write(json.dumps(export, indent=4))
        except IOError as e:
            _LOGGER.error(f"Error writing HA shopping list to {self._hasl_path}: {e}")

    async def refresh(self) -> None:
        """Refresh the HA shopping list."""
        await self._hasl_refresh()
