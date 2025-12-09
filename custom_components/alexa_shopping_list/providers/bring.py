#!/usr/bin/env python3

"""Bring shopping list integration provider."""

from typing import List
import logging
from homeassistant.exceptions import HomeAssistantError
from .base import ShoppingListProvider

_LOGGER = logging.getLogger(__name__)


class BringShoppingListProvider(ShoppingListProvider):
    """Provider for Bring shopping list integration."""

    def __init__(self, hass, bring_list: str = None):
        """Initialize the Bring shopping list provider.
        
        Args:
            hass: Home Assistant instance
            bring_list: Name of the Bring list to sync with (without the sensor. prefix)
                        If None, will attempt to find the first available Bring sensor
        """
        super().__init__(hass)
        self._bring_list = bring_list

    def _is_entity_id(self, value: str) -> bool:
        """Check if value is a full entity ID.
        
        Args:
            value: String to check
            
        Returns:
            True if value starts with 'sensor.'
        """
        return value and value.startswith("sensor.")

    def _get_entity_id(self) -> str:
        """Get the Bring sensor entity ID.
        
        Returns:
            Entity ID for the Bring sensor, or None if not configured
        """
        if self._bring_list:
            # Allow full entity_id or just the name
            if self._is_entity_id(self._bring_list):
                return self._bring_list
            return f"sensor.{self._bring_list}"
        
        # Try to find the first Bring sensor
        for entity_id in self.hass.states.async_entity_ids("sensor"):
            if entity_id.startswith("sensor.bring"):
                _LOGGER.info(f"Auto-detected Bring entity: {entity_id}")
                return entity_id
        
        return None

    def _build_service_data(self, item: str) -> dict:
        """Build service data for Bring service calls.
        
        Args:
            item: Item name
            
        Returns:
            Service data dictionary
        """
        service_data = {"item": item}
        
        # Add list parameter if a specific list is configured (not an entity ID)
        if self._bring_list and not self._is_entity_id(self._bring_list):
            service_data["list"] = self._bring_list
        
        return service_data

    async def read_list(self) -> List[dict]:
        """Read the current Bring shopping list.
        
        Returns:
            List of items with format: [{"name": str, "complete": bool}, ...]
        """
        items = []
        
        # Get the Bring sensor entity
        entity_id = self._get_entity_id()
        if entity_id is None:
            _LOGGER.error("No Bring entity configured or found")
            return items
            
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
        service_data = self._build_service_data(item)
        
        try:
            await self.hass.services.async_call(
                "bring",
                "add_item",
                service_data,
                blocking=True
            )
            _LOGGER.debug(f"Added item '{item}' to Bring list")
        except HomeAssistantError as e:
            _LOGGER.error(f"Failed to add item '{item}' to Bring: {e}")
        except Exception as e:
            _LOGGER.error(f"Unexpected error adding item '{item}' to Bring: {e}")

    async def _remove_from_bring(self, item: str) -> None:
        """Remove an item from the Bring list.
        
        Args:
            item: Item name to remove
        """
        service_data = self._build_service_data(item)
        
        try:
            await self.hass.services.async_call(
                "bring",
                "remove_item",
                service_data,
                blocking=True
            )
            _LOGGER.debug(f"Removed item '{item}' from Bring list")
        except HomeAssistantError as e:
            _LOGGER.error(f"Failed to remove item '{item}' from Bring: {e}")
        except Exception as e:
            _LOGGER.error(f"Unexpected error removing item '{item}' from Bring: {e}")

    async def refresh(self) -> None:
        """Refresh the Bring shopping list.
        
        Bring integration automatically updates, so this is a no-op.
        """
        pass
