"""Writes menu data from the coordinator into a Home Assistant calendar entity.

Called by the sync_menu service handler in __init__.py.

Strategy to avoid duplicate events on repeated syncs:
  1. Query the calendar for existing events over the date range we are about
     to write (this week + next week).
  2. Delete any event whose summary starts with our ownership marker prefix.
  3. Create fresh events for every day that has menu data.

The HA Local Calendar integration supports calendar.list_events (returns a
list of CalendarEvent-like dicts) and calendar.delete_event (takes a uid).
"""
from __future__ import annotations

import datetime
import logging
from typing import Any

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# All events we own start with this string so we can identify and clean them up
EVENT_PREFIX = "🏫 Chenoweth –"

# How many weeks ahead we manage events for
WEEKS_AHEAD = 2


async def write_calendar_events(
    hass: HomeAssistant,
    calendar_entity_id: str,
    menu_data: dict[str, Any],
) -> None:
    """Idempotently write one calendar event per school day in menu_data.

    menu_data shape:
        {"2026-04-07": {"breakfast": [...], "lunch": [...]}, ...}
    """
    today = datetime.date.today()
    range_start = _week_start(today)
    range_end = range_start + datetime.timedelta(weeks=WEEKS_AHEAD)

    await _delete_owned_events(hass, calendar_entity_id, range_start, range_end)

    for date_str, meals in sorted(menu_data.items()):
        breakfast_items: list[dict] = meals.get("breakfast", [])
        lunch_items: list[dict] = meals.get("lunch", [])

        if not breakfast_items and not lunch_items:
            continue

        summary = f"{EVENT_PREFIX} {_friendly_date(date_str)}"
        description = _build_description(breakfast_items, lunch_items)
        hero_image = _pick_hero_image(lunch_items or breakfast_items)

        try:
            await hass.services.async_call(
                "calendar",
                "create_event",
                {
                    "entity_id": calendar_entity_id,
                    "summary": summary,
                    "description": description,
                    # School-day hours
                    "start_date_time": f"{date_str}T08:00:00",
                    "end_date_time": f"{date_str}T15:00:00",
                    # HA Local Calendar has a free-text location field;
                    # we store the hero image URL here for easy dashboard use.
                    "location": hero_image,
                },
                blocking=True,
            )
            _LOGGER.debug("Created calendar event: %s", summary)
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Failed to create event for %s: %s", date_str, err)


# ── Private helpers ───────────────────────────────────────────────────────────

async def _delete_owned_events(
    hass: HomeAssistant,
    calendar_entity_id: str,
    range_start: datetime.date,
    range_end: datetime.date,
) -> None:
    """Delete all events we previously created in the given date range."""
    try:
        result = await hass.services.async_call(
            "calendar",
            "list_events",
            {
                "entity_id": calendar_entity_id,
                "start_date_time": f"{range_start}T00:00:00",
                "end_date_time": f"{range_end}T23:59:59",
            },
            blocking=True,
            return_response=True,
        )
    except Exception as err:  # noqa: BLE001
        _LOGGER.debug(
            "Could not list calendar events for cleanup (non-fatal): %s", err
        )
        return

    events: list[dict] = []
    if isinstance(result, dict):
        # Response shape: {"events": [...]}
        events = result.get("events", [])

    deleted = 0
    for event in events:
        summary: str = event.get("summary", "")
        uid: str = event.get("uid", "")
        if summary.startswith(EVENT_PREFIX) and uid:
            try:
                await hass.services.async_call(
                    "calendar",
                    "delete_event",
                    {"entity_id": calendar_entity_id, "uid": uid},
                    blocking=True,
                )
                deleted += 1
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Could not delete event uid=%s: %s", uid, err)

    if deleted:
        _LOGGER.debug("Deleted %d stale menu event(s) from %s", deleted, calendar_entity_id)


def _week_start(ref: datetime.date) -> datetime.date:
    return ref - datetime.timedelta(days=ref.weekday())


def _friendly_date(date_str: str) -> str:
    d = datetime.date.fromisoformat(date_str)
    return d.strftime("%A, %b %-d")


def _pick_hero_image(items: list[dict]) -> str:
    return next((i["image"] for i in items if i.get("image")), "")


def _build_description(breakfast: list[dict], lunch: list[dict]) -> str:
    lines: list[str] = []

    if breakfast:
        lines.append("🍳 BREAKFAST")
        lines.extend(f"  • {i['name']}" for i in breakfast)

    if lunch:
        if lines:
            lines.append("")
        lines.append("🥗 LUNCH")
        lines.extend(f"  • {i['name']}" for i in lunch)

    return "\n".join(lines)
