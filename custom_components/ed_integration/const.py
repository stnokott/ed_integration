"""Constants for ed_integration."""
# Base component constants
NAME = "ED Integration"
DOMAIN = "ed_integration"
VERSION = "0.0.1"

ISSUE_URL = "https://github.com/custom-components/blueprint/issues"

# ED
KEY_CMDR_NAME = "cmdr_name"
KEY_EDSM_API_KEY = "edsm_api_key"
KEY_INARA_API_KEY = "inara_api_key"
KEY_POP_SYSTEMS_REFRESH_INTERVAL = "pop_systems_refresh_interval"

KEY_OUTPUT_LOCATION_STR = "location_str"
KEY_OUTPUT_BALANCE_STR = "balance_str"

# Icons
ICON_LOCATION = "mdi:map-marker"
ICON_BALANCE = "mdi:cash"

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is the Elite Dangerous integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
