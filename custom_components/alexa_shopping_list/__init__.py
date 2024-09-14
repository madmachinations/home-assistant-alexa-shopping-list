#!/usr/bin/env python3

import logging

from .asl import AlexaShoppingListSync

_LOGGER = logging.getLogger(__name__)

DOMAIN = "alexa_shopping_list"

CONF_IP = "server_ip"
CONF_PORT = "server_port"
CONF_SYNC_MINS = "sync_mins"

SERVICE_SYNC = "sync_alexa_shopping_list"


async def async_setup_entry(hass, entry):
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})

    try:

        alexa = AlexaShoppingListSync(
            entry.data[CONF_IP],
            entry.data[CONF_PORT],
            entry.data[CONF_SYNC_MINS],
            hass.config.path(".shopping_list.json"),
            hass.data["shopping_list"].async_load
        )

    except Exception as e:
        _LOGGER.error(f"Error during async_setup_entry: {e}", exc_info=True)
        return False
    
    # hass.bus.async_listen("shopping_list_updated", alexa.homeassistant_shopping_list_updated)
    hass.data[DOMAIN][entry.entry_id] = alexa
    await hass.config_entries.async_forward_entry_setup(entry, "sensor")

    services = AlexaServices(alexa, _LOGGER)
    hass.services.async_register(DOMAIN, SERVICE_SYNC, services.handle_sync_service)

    return True


class AlexaServices:

    def __init__(self, alexa, logger):
        self.alexa = alexa
        self.logger = logger

    async def handle_sync_service(self, call):
        self.logger.debug("Alexa Sync Service")

        try:
            await self.alexa.sync(self.logger, True)
        except Exception as e:
            self.logger.error(f"Alexa Shopping List Sync Error: {e}", exc_info=True)


