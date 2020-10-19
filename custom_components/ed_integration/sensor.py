"""Sensor platform for ed_integration."""
from custom_components.ed_integration.const import DOMAIN, ICON
from custom_components.ed_integration.entity import EDEntity

from .const import (
    KEY_CMDR_NAME,
    KEY_POP_SYSTEMS_REFRESH_INTERVAL
)


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices([EDSensor(coordinator, entry)])


class EDSensor(EDEntity):
    """ed_integration Sensor class."""

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"Refresh every {self.config_entry.data[KEY_POP_SYSTEMS_REFRESH_INTERVAL]}"

    @property
    def state(self):
        """Return the state of the sensor."""
        self.config_entry.data.get(KEY_CMDR_NAME)
        return self.coordinator.data.get("static")

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON
