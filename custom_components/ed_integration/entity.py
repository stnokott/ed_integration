"""BlueprintEntity class"""
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.ed_integration.const import DOMAIN, NAME, VERSION


class EDEntity(CoordinatorEntity):
    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator)
        self.config_entry = config_entry

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return self.config_entry.entry_id

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
