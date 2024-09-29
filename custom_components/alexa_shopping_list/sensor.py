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

    alexa = hass.data[DOMAIN][config_entry.entry_id]

    update_sensor = AlexaShoppingListSyncSensor(hass, alexa)

    async_add_entities([update_sensor], update_before_add=True)


class AlexaShoppingListSyncSensor(SensorEntity):
    """Synchronise HA and Alexa shopping lists"""

    def __init__(self, hass, alexa):
        self.hass = hass
        self.alexa = alexa

        self._attr_name = "Alexa Shopping List Sync"
        self._attr_icon = "mdi:sync"
        self._attr_unique_id = "alexa_shopping_list_sync"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
    

    async def async_update(self) -> None:
        try:

            updated = await self.alexa.sync(_LOGGER)
            if updated == True:
                _LOGGER.debug("Firing alexa_shopping_list_changed event")
                self.hass.bus.async_fire("alexa_shopping_list_changed")

        except Exception as e:
            _LOGGER.error(f"Alexa Shopping List Sync Error: {e}", exc_info=True)
        self._attr_native_value = self.alexa.last_updated
