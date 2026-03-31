"""Config flow for Chenoweth Elementary Menu integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import CONF_CALENDAR_ENTITY, DEFAULT_CALENDAR_ENTITY, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CALENDAR_ENTITY, default=DEFAULT_CALENDAR_ENTITY): (
            selector.EntitySelector(
                selector.EntitySelectorConfig(domain="calendar")
            )
        ),
    }
)


class ChenowethMenuConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup flow shown in the HA Integrations UI."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show the configuration form; create the entry on valid submit."""
        if user_input is not None:
            # single_config_entry in manifest.json already prevents a second
            # entry, but setting a unique_id lets HA surface a clean
            # "already configured" abort message.
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title="Chenoweth Elementary Menu",
                data={CONF_CALENDAR_ENTITY: user_input[CONF_CALENDAR_ENTITY]},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
        )
