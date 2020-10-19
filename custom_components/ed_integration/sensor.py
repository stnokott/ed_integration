"""Sensor platform for ed_integration."""
from custom_components.ed_integration.const import DEFAULT_NAME, DOMAIN, ICON
from custom_components.ed_integration.entity import EDEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices([EDSensor(coordinator, entry)])


class EDSensor(EDEntity):
    """ed_integration Sensor class."""

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{DEFAULT_NAME}_sensor"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get("static")

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON
