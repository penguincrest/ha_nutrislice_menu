"""Chenoweth Elementary Menu – Home Assistant Custom Integration.

Fetches breakfast and lunch menus from the JCPS Nutrislice API and:
  • Creates two sensor entities (today's breakfast / lunch)
  • Registers a service  chenoweth_menu.sync_menu  that fetches fresh
    data from Nutrislice and writes events to a chosen calendar entity

Scheduling is entirely up to the user – create an HA automation that calls
chenoweth_menu.sync_menu on whatever cadence you want.
"""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall

from .calendar_writer import write_calendar_events
from .const import (
    CONF_CALENDAR_ENTITY,
    DATA_CALENDAR_ENTITY,
    DATA_COORDINATOR,
    DEFAULT_CALENDAR_ENTITY,
    DOMAIN,
    SERVICE_SYNC_MENU,
)
from .coordinator import NutrisliceCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the integration from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = NutrisliceCoordinator(hass)

    # async_config_entry_first_refresh() automatically converts UpdateFailed
    # into ConfigEntryNotReady so HA will retry – no extra wrapping needed.
    await coordinator.async_config_entry_first_refresh()

    calendar_entity_id: str = entry.data.get(
        CONF_CALENDAR_ENTITY, DEFAULT_CALENDAR_ENTITY
    )

    hass.data[DOMAIN][entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
        DATA_CALENDAR_ENTITY: calendar_entity_id,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # ── Register the sync_menu service ───────────────────────────────────────
    async def handle_sync_menu(call: ServiceCall) -> None:
        """Fetch fresh Nutrislice data, update sensors, write calendar events."""
        _LOGGER.info("chenoweth_menu.sync_menu called – fetching menus…")

        await coordinator.async_refresh()

        if not coordinator.data:
            _LOGGER.warning("sync_menu: no data returned from Nutrislice")
            return

        await write_calendar_events(hass, calendar_entity_id, coordinator.data)
        _LOGGER.info(
            "sync_menu complete – %d days written to %s",
            len(coordinator.data),
            calendar_entity_id,
        )

    # Guard against duplicate registration on config-entry reload
    if not hass.services.has_service(DOMAIN, SERVICE_SYNC_MENU):
        hass.services.async_register(DOMAIN, SERVICE_SYNC_MENU, handle_sync_menu)
        _LOGGER.debug("Registered service %s.%s", DOMAIN, SERVICE_SYNC_MENU)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the integration cleanly."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        # Only remove the service when the very last config entry is gone
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_SYNC_MENU)

    return unload_ok
