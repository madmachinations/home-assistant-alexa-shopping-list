#!/usr/bin/env python3

import logging

from .asl import AlexaShoppingListSync
from .providers import HAShoppingListProvider, BringShoppingListProvider

_LOGGER = logging.getLogger(__name__)

DOMAIN = "alexa_shopping_list"

CONF_IP = "server_ip"
CONF_PORT = "server_port"
CONF_SYNC_MINS = "sync_mins"
CONF_PROVIDER = "provider"

SERVICE_SYNC = "sync_alexa_shopping_list"

PROVIDER_HA = "ha_shopping_list"
PROVIDER_BRING = "bring"


async def async_setup_entry(hass, entry):
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})

    try:
        # Get provider type from config, default to HA shopping list
        provider_type = entry.data.get(CONF_PROVIDER, PROVIDER_HA)
        
        # Create the appropriate provider
        if provider_type == PROVIDER_BRING:
            provider = BringShoppingListProvider(hass)
        else:
            # Default to HA shopping list provider
            provider = HAShoppingListProvider(
                hass,
                hass.config.path(".shopping_list.json"),
                hass.data["shopping_list"].async_load
            )

        alexa = AlexaShoppingListSync(
            entry.data[CONF_IP],
            entry.data[CONF_PORT],
            entry.data[CONF_SYNC_MINS],
            provider
        )

    except Exception as e:
        _LOGGER.error(f"Error during async_setup_entry: {e}", exc_info=True)
        return False
    
    # hass.bus.async_listen("shopping_list_updated", alexa.homeassistant_shopping_list_updated)
    hass.data[DOMAIN][entry.entry_id] = alexa
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    services = AlexaServices(alexa, _LOGGER, hass)
    hass.services.async_register(DOMAIN, SERVICE_SYNC, services.handle_sync_service)

    return True


class AlexaServices:

    def __init__(self, alexa, logger, hass):
        self.alexa = alexa
        self.logger = logger
        self.hass = hass

    async def handle_sync_service(self, call):
        self.logger.debug("Alexa Sync Service")

        try:
            updated = await self.alexa.sync(self.logger, True)
            if updated == True:
                _LOGGER.debug("Firing alexa_shopping_list_changed event")
                self.hass.bus.async_fire("alexa_shopping_list_changed")
        except Exception as e:
            self.logger.error(f"Alexa Shopping List Sync Error: {e}", exc_info=True)


