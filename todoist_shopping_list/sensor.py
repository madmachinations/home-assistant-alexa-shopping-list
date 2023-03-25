#!/usr/bin/env python3

import logging
import json

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity
)

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup sensors from a config entry created in the integrations UI."""

    api = hass.data[DOMAIN][config_entry.entry_id]

    update_sensor = TodoistShoppingListSyncSensor(hass, api)

    async_add_entities([update_sensor], update_before_add=True)


class TodoistShoppingListSyncSensor(SensorEntity):
    """Synchronise HA and Todoist shopping lists"""

    def __init__(self, hass, api):
        self.hass = hass
        self.api = api

        self._attr_name = "Todoist Shopping List Sync"
        self._attr_icon = "mdi:sync"
        self._attr_unique_id = "todoist_shopping_list_sync"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
    

    async def async_update(self) -> None:
        current_hash = self.api.get_shopping_list_hash()
        await self.api.update()

        if current_hash != self.api.get_shopping_list_hash():
            await self.api.export_shopping_list()

        self._attr_native_value = self.api.last_updated
