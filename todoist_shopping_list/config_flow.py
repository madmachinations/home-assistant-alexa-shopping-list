"""Config flow"""
from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaFlowFormStep,
    SchemaOptionsFlowHandler,
)

from . import DOMAIN, CONF_API_KEY

_LOGGER = logging.getLogger(__name__)


class TfgmConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        pass


    async def async_step_user(self, user_input=None):
        """Invoked when a user initiates a flow via the user interface."""

        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="Todoist Shopping List", data={
                CONF_API_KEY: user_input[CONF_API_KEY]
            })

        return self.async_show_form(step_id="user", data_schema=vol.Schema({
            vol.Required(CONF_API_KEY): cv.string
        }), errors=errors)