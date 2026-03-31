"""Constants for the Chenoweth Elementary Menu integration."""

DOMAIN = "chenoweth_menu"

# Nutrislice
DISTRICT = "jcps"
SCHOOL_SLUG = "chenoweth"
NUTRISLICE_API_URL = (
    "https://{district}.api.nutrislice.com"
    "/menu/api/weeks/school/{school}"
    "/menu-type/{menu_type}/{year}/{month:02d}/{day:02d}/"
)

MENU_TYPE_BREAKFAST = "breakfast"
MENU_TYPE_LUNCH = "lunch"

# Food categories we surface; empty string catches uncategorised items
KEEP_CATEGORIES = {"entree", "side", "fruit", "vegetable", "grain", "protein", ""}

# Calendar entity written to
CONF_CALENDAR_ENTITY = "calendar_entity"
DEFAULT_CALENDAR_ENTITY = "calendar.school_menu"

# hass.data keys
DATA_COORDINATOR = "coordinator"
DATA_CALENDAR_ENTITY = "calendar_entity"

# Service
SERVICE_SYNC_MENU = "sync_menu"
