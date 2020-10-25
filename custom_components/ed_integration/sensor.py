"""Sensor platform for ed_integration."""
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.ed_integration.const import DOMAIN, ICON_LOCATION

from .const import KEY_CMDR_NAME, KEY_OUTPUT_LOCATION_STR, NAME, VERSION


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    cmdr_name = entry.data.get(KEY_CMDR_NAME)
    async_add_devices([EDLocationSensor(coordinator, cmdr_name)])


class EDLocationSensor(CoordinatorEntity):
    """ed_integration Sensor class."""

    def __init__(self, coordinator, cmdr_name):
        super().__init__(coordinator)
        self._cmdr_name = cmdr_name

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        cmdr_name_id = self._cmdr_name.replace(" ", "_")
        return f"{cmdr_name_id}_location"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"CMDR {self._cmdr_name}"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": NAME,
            "model": VERSION,
            "manufacturer": NAME,
        }

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            "static": self.coordinator.data.get("static"),
            "time": self.coordinator.data.get("time")
        }

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get(KEY_OUTPUT_LOCATION_STR)

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON_LOCATION
