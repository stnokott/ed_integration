"""Sensor platform for ed_integration."""
from custom_components.ed_integration.const import DOMAIN, ICON_LOCATION
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import KEY_CMDR_NAME, KEY_OUTPUT_LOCATION_STR, KEY_OUTPUT_BALANCE_STR, ICON_BALANCE


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    cmdr_name = entry.data.get(KEY_CMDR_NAME)
    async_add_entities([EDLocationSensor(coordinator, cmdr_name), EDBalanceSensor(coordinator, cmdr_name)])


class EDLocationSensor(CoordinatorEntity):
    """CMDR location sensor class."""

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
        return f"CMDR {self._cmdr_name} Location"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get(KEY_OUTPUT_LOCATION_STR)

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON_LOCATION


class EDBalanceSensor(CoordinatorEntity):
    """CMDR credits balance sensor class."""

    def __init__(self, coordinator, cmdr_name):
        super().__init__(coordinator)
        self._cmdr_name = cmdr_name

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        cmdr_name_id = self._cmdr_name.replace(" ", "_")
        return f"{cmdr_name_id}_balance"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"CMDR {self._cmdr_name} Balance"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get(KEY_OUTPUT_BALANCE_STR)

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement"""
        return "credits"

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON_BALANCE
