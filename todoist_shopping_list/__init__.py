#!/usr/bin/env python3

import logging
from .todoist import Todoist

_LOGGER = logging.getLogger(__name__)

DOMAIN = "todoist_shopping_list"
CONF_API_KEY = "api_key"


async def async_setup_entry(hass, entry):
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})

    api = Todoist(entry.data[CONF_API_KEY])
    await api.connect()

    if api.failed == False:

        api.set_ha_shopping_list(
            hass.config.path(".shopping_list.json"),
            hass.data["shopping_list"].async_load
        )

        await api.export_shopping_list()

        hass.bus.async_listen("shopping_list_updated", api.homeassistant_shopping_list_updated)

        hass.data[DOMAIN][entry.entry_id] = api

        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, "sensor")
        )

        return True
    
    else:
        return False