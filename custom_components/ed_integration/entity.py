"""ED Sensor superclass"""

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME, VERSION


class EDEntity(CoordinatorEntity):
    """Superclass for sensor entities"""
    @property
    def device_info(self):
        """Provide device information data"""
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