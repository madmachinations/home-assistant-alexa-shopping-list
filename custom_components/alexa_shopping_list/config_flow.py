"""Config flow to configure Alexa Shopping List."""
from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any
import os

import voluptuous as vol

from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv

from .asl import AlexaShoppingListSync

from . import DOMAIN, CONF_IP, CONF_PORT, CONF_SYNC_MINS

_LOGGER = logging.getLogger(__name__)


class AlexaShoppingListConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self.config_data = {}


    async def async_step_user(self, user_input=None):
        """Invoked when a user initiates a flow via the user interface."""
        return await self.async_step_server()
    

    def _save_config(self):
        return self.async_create_entry(title="Alexa Shopping List", data={
            CONF_IP: self.config_data[CONF_IP],
            CONF_PORT: self.config_data[CONF_PORT],
            CONF_SYNC_MINS: self.config_data[CONF_SYNC_MINS],
        })
    

    async def async_step_server(self, user_input=None):
        errors = {}

        if user_input is not None:
            self.config_data[CONF_IP] = user_input[CONF_IP]
            self.config_data[CONF_PORT] = int(user_input[CONF_PORT])

            alexa = AlexaShoppingListSync(
                self.config_data[CONF_IP],
                self.config_data[CONF_PORT]
            )

            if await alexa.can_ping_server() == True:
                if await alexa.server_config_is_valid() == True:
                    if await alexa.server_is_authenticated() == True:
                        return await self.async_step_sync_mins()
                    else:
                        errors["base"] = "server_not_authenticated"
                else:
                    errors["base"] = "server_not_setup"
            else:
                errors["base"] = "connection_failed"

        return self.async_show_form(step_id="server", data_schema=vol.Schema({
            vol.Required(CONF_IP, default="localhost"): cv.string,
            vol.Required(CONF_PORT, default="4000"): cv.string,
        }), errors=errors)


    async def async_step_sync_mins(self, user_input=None):
        errors = {}

        if user_input is not None:
            sync_mins = user_input[CONF_SYNC_MINS]
            if sync_mins == "" or sync_mins == None:
                sync_mins = 60
            
            self.config_data[CONF_SYNC_MINS] = int(sync_mins)
            return self._save_config()

        return self.async_show_form(step_id="sync_mins", data_schema=vol.Schema({
            vol.Required(CONF_SYNC_MINS, default="60"): cv.string,
        }), errors=errors)