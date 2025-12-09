#!/usr/bin/env python3

"""Bring shopping list integration provider."""

from typing import List
import logging
from .base import ShoppingListProvider

_LOGGER = logging.getLogger(__name__)


class BringShoppingListProvider(ShoppingListProvider):
    """Provider for Bring shopping list integration."""

    def __init__(self, hass, bring_list: str = ""):
        """Initialize the Bring shopping list provider.
        
        Args:
            hass: Home Assistant instance
            bring_list: Name/entity ID of the Bring list to sync with
        """
        super().__init__(hass)
        self._bring_list = bring_list or "bring"

    async def read_list(self) -> List[dict]:
        """Read the current Bring shopping list.
        
        Returns:
            List of items with format: [{"name": str, "complete": bool}, ...]
        """
        items = []
        
        # Get the Bring sensor entity
        entity_id = f"sensor.{self._bring_list}"
        state = self.hass.states.get(entity_id)
        
        if state is None:
            _LOGGER.warning(f"Bring entity {entity_id} not found")
            return items
        
        # The Bring integration stores items in the state attributes
        attributes = state.attributes
        
        # Get purchase list (uncompleted items)
        purchase = attributes.get("purchase", [])
        for item in purchase:
            items.append({
                "name": item,
                "complete": False
            })
        
        # Get recently list (completed items)
        recently = attributes.get("recently", [])
        for item in recently:
            items.append({
                "name": item,
                "complete": True
            })
        
        return items

    async def export_list(self, items: List[str]) -> None:
        """Export items to Bring shopping list.
        
        Args:
            items: List of item names to sync to the Bring shopping list
        """
        # Get current Bring list items
        current_items = await self.read_list()
        
        # Determine what's currently on the purchase list (not completed)
        current_purchase = {item["name"] for item in current_items if not item["complete"]}
        
        # Items that need to be on the list
        target_items = set(items)
        
        # Add missing items
        to_add = target_items - current_purchase
        for item in to_add:
            await self._add_to_bring(item)
        
        # Remove items that shouldn't be there anymore
        to_remove = current_purchase - target_items
        for item in to_remove:
            await self._remove_from_bring(item)

    async def _add_to_bring(self, item: str) -> None:
        """Add an item to the Bring list.
        
        Args:
            item: Item name to add
        """
        service_data = {
            "item": item,
        }
        
        # If a specific list is configured, add it to the service data
        if self._bring_list and self._bring_list != "bring":
            service_data["list"] = self._bring_list
        
        try:
            await self.hass.services.async_call(
                "bring",
                "add_item",
                service_data,
                blocking=True
            )
            _LOGGER.debug(f"Added item '{item}' to Bring list")
        except Exception as e:
            _LOGGER.error(f"Failed to add item '{item}' to Bring: {e}")

    async def _remove_from_bring(self, item: str) -> None:
        """Remove an item from the Bring list.
        
        Args:
            item: Item name to remove
        """
        service_data = {
            "item": item,
        }
        
        # If a specific list is configured, add it to the service data
        if self._bring_list and self._bring_list != "bring":
            service_data["list"] = self._bring_list
        
        try:
            await self.hass.services.async_call(
                "bring",
                "remove_item",
                service_data,
                blocking=True
            )
            _LOGGER.debug(f"Removed item '{item}' from Bring list")
        except Exception as e:
            _LOGGER.error(f"Failed to remove item '{item}' from Bring: {e}")

    async def refresh(self) -> None:
        """Refresh the Bring shopping list.
        
        Bring integration automatically updates, so this is a no-op.
        """
        pass
