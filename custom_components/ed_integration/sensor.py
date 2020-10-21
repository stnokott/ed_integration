"""Sensor platform for ed_integration."""
from custom_components.ed_integration.const import DOMAIN, ICON_LOCATION
from custom_components.ed_integration.entity import EDEntity

from .const import KEY_CMDR_NAME, KEY_OUTPUT_LOCATION_STR


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices([EDLocationSensor(coordinator, entry)])


class EDLocationSensor(EDEntity):
    """ed_integration Sensor class."""

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"CMDR {self.config_entry.data.get(KEY_CMDR_NAME)}"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get(KEY_OUTPUT_LOCATION_STR)

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON_LOCATION
