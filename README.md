# Chenoweth Elementary Menu – HA Custom Integration

A proper Home Assistant custom integration (not an AppDaemon app) that pulls
breakfast and lunch menus from the JCPS Nutrislice API and:

- Creates **two sensor entities** with today's menu items + food images
- Registers a **service** (`chenoweth_menu.sync_menu`) that fetches menus and
  writes events to any HA calendar entity you choose
- Adds a **UI config flow** so setup is done entirely through Settings → Integrations

Scheduling is 100% in your hands – call `chenoweth_menu.sync_menu` from your
own automation whenever you like.

---

## File structure

```
custom_components/chenoweth_menu/
├── __init__.py          ← integration setup / teardown / service handler
├── manifest.json        ← HA integration metadata
├── config_flow.py       ← UI setup wizard
├── const.py             ← all constants
├── coordinator.py       ← DataUpdateCoordinator (Nutrislice API client)
├── calendar_writer.py   ← writes coordinator data to a HA calendar
├── sensor.py            ← two sensor entities (breakfast today / lunch today)
├── services.yaml        ← service schema
├── strings.json         ← UI text
└── translations/
    └── en.json          ← English translations
```

---

## Installation

### Manual (recommended for this integration)

1. Copy the `custom_components/chenoweth_menu/` folder into your HA config
   directory so the path is:
   ```
   /config/custom_components/chenoweth_menu/
   ```
2. Restart Home Assistant.

---

## Setup

### 1. Create a Local Calendar for the menus

Go to **Settings → Integrations → + Add Integration → Local Calendar**.
Name it **School Menu** → entity becomes `calendar.school_menu`.

### 2. Add the integration

Go to **Settings → Integrations → + Add Integration**, search for
**Chenoweth Elementary Menu**, and follow the single-step wizard.

When prompted, pick the calendar entity you just created (`calendar.school_menu`).

HA will immediately perform a first data fetch from Nutrislice so the sensor
entities are populated right away.

### 3. Add an automation to call the sync service

The integration creates the service `chenoweth_menu.sync_menu` but **never
calls it automatically**. Create an automation in HA using the example in
`automation_example.yaml` (Sunday evening + Monday morning are a good
combination to keep the whole upcoming week populated).

You can also call it manually any time from:
**Developer Tools → Services → chenoweth_menu.sync_menu → Call Service**

---

## Entities created

| Entity | Description |
|---|---|
| `sensor.chenoweth_breakfast_today` | Today's breakfast items (comma-separated) |
| `sensor.chenoweth_lunch_today` | Today's lunch items (comma-separated) |

Both sensors also expose these attributes:

| Attribute | Description |
|---|---|
| `items` | Full list of `{name, category, image}` dicts |
| `hero_image` | URL of the first food image (useful for notifications) |
| `meal_type` | `breakfast` or `lunch` |
| `date` | ISO date string for today |

---

## Service

### `chenoweth_menu.sync_menu`

Fetches this week's and next week's menus from Nutrislice, updates the sensor
entities, and creates calendar events for each school day.

**No parameters required.**

---

## Lovelace card

Paste `lovelace_card.yaml` into a Manual card on your dashboard for a card
that shows today's items with food images and a weekly calendar view.

---

## How the Nutrislice API works

The API is public and requires no key:
```
https://jcps.api.nutrislice.com/menu/api/weeks/school/chenoweth/menu-type/{breakfast|lunch}/{YYYY}/{MM}/{DD}/
```
Two requests are made per sync (one per meal type, per week = 4 total for
this week + next week).

If JCPS ever renames the Nutrislice school slug, update `SCHOOL_SLUG` in
`const.py`.
