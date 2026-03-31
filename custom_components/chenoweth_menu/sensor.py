"""Sensor platform for Chenoweth Elementary Menu.

Creates two sensors:
  sensor.chenoweth_breakfast_today  – today's breakfast items (state = comma list)
  sensor.chenoweth_lunch_today      – today's lunch items      (state = comma list)

Each sensor also exposes `items` and `hero_image` as extra state attributes so
dashboards and automations can access richer data without parsing the state.
"""
from __future__ import annotations

import datetime
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATOR, DOMAIN, MENU_TYPE_BREAKFAST, MENU_TYPE_LUNCH
from .coordinator import NutrisliceCoordinator

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0  # coordinator-based; no individual polling


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities from a config entry."""
    coordinator: NutrisliceCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    async_add_entities(
        [
            ChenowethMenuSensor(coordinator, MENU_TYPE_BREAKFAST, entry.entry_id),
            ChenowethMenuSensor(coordinator, MENU_TYPE_LUNCH, entry.entry_id),
        ],
        update_before_add=False,  # coordinator already fetched on setup
    )


class ChenowethMenuSensor(CoordinatorEntity[NutrisliceCoordinator], SensorEntity):
    """A sensor that surfaces today's menu items for one meal type."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:silverware-fork-knife"

    def __init__(
        self,
        coordinator: NutrisliceCoordinator,
        meal_type: str,
        entry_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._meal_type = meal_type
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{meal_type}_today"
        self._attr_name = f"{meal_type.capitalize()} Today"

        # DeviceInfo is required when has_entity_name=True so HA knows which
        # device to group these sensors under in the entity registry.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Chenoweth Elementary Menu",
            manufacturer="JCPS / Nutrislice",
            model="School Menu",
            entry_type="service",
        )

    # ── State ────────────────────────────────────────────────────────────────

    @property
    def native_value(self) -> str | None:
        """Return today's menu items as a comma-separated string, or None."""
        items = self._today_items()
        if not items:
            return None
        return ", ".join(i["name"] for i in items)

    # ── Extra attributes ─────────────────────────────────────────────────────

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        items = self._today_items()
        hero = next((i["image"] for i in items if i.get("image")), "")
        return {
            "items": items,
            "hero_image": hero,
            "meal_type": self._meal_type,
            "date": datetime.date.today().isoformat(),
        }

    # ── Internal ─────────────────────────────────────────────────────────────

    def _today_items(self) -> list[dict[str, str]]:
        if not self.coordinator.data:
            return []
        today = datetime.date.today().isoformat()
        return self.coordinator.data.get(today, {}).get(self._meal_type, [])
