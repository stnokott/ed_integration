"""
Custom integration to integrate ed_integration with Home Assistant.

For more details about this integration, please refer to
https://github.com/custom-components/blueprint
"""
import asyncio
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from custom_components.ed_integration.const import (
    DOMAIN,
    PLATFORMS,
    STARTUP_MESSAGE,
    KEY_CMDR_NAME,
    KEY_EDSM_API_KEY,
    KEY_INARA_API_KEY,
    KEY_POP_SYSTEMS_REFRESH_INTERVAL,
)

from .client import (Configuration, Client)

SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: Config):
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    cmdr_name = entry.data.get(KEY_CMDR_NAME)
    edsm_api_key = entry.data.get(KEY_EDSM_API_KEY)
    inara_api_key = entry.data.get(KEY_INARA_API_KEY)
    pop_systems_refresh_interval = entry.data.get(KEY_POP_SYSTEMS_REFRESH_INTERVAL)

    coordinator = EDDataUpdateCoordinator(
        hass, cmdr_name, edsm_api_key, inara_api_key, pop_systems_refresh_interval
    )
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = coordinator

    for platform in PLATFORMS:
        if entry.options.get(platform, True):
            coordinator.platforms.append(platform)
            hass.async_add_job(
                hass.config_entries.async_forward_entry_setup(entry, platform)
            )

    entry.add_update_listener(async_reload_entry)
    return True


class EDDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass, cmdr_name, edsm_api_key, inara_api_key, pop_systems_refresh_interval):
        """Initialize."""
        config = Configuration(cmdr_name, edsm_api_key, inara_api_key, pop_systems_refresh_interval)
        self.api = Client(config)
        self.platforms = []

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

    async def _async_update_data(self):
        """Update data via library."""
        try:
            data = await self.api.async_get_data()
            return data.get("data", {})
        except Exception as exception:
            raise UpdateFailed(exception)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Handle removal of an entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
                if platform in coordinator.platforms
            ]
        )
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
