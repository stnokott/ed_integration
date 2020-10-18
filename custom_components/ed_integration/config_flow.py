"""Adds config flow for Blueprint."""
from collections import OrderedDict
from homeassistant import config_entries
from homeassistant.core import callback
import voluptuous as vol

from .const import (
    DOMAIN,
    KEY_CMDR_NAME,
    KEY_EDSM_API_KEY,
    KEY_INARA_API_KEY,
    KEY_POP_SYSTEMS_REFRESH_INTERVAL,
)


class EDFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Blueprint."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        # only one instance allowed
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            if KEY_POP_SYSTEMS_REFRESH_INTERVAL not in user_input:
                user_input[KEY_POP_SYSTEMS_REFRESH_INTERVAL] = 24

            if user_input[KEY_POP_SYSTEMS_REFRESH_INTERVAL] <= 0:
                self._errors[KEY_POP_SYSTEMS_REFRESH_INTERVAL] = "invalid_value_error"

            else:
                # TODO: test valid
                return self.async_create_entry(
                    title="Elite Dangerous Configuration",
                    data=user_input
                )
            return await self._show_config_form(user_input)

        return await self._show_config_form(user_input)

    # @staticmethod
    # @callback
    # def async_get_options_flow(config_entry):
    #     """Get new ConfigFlow instance"""
    #     return EDOptionsFlowHandler(config_entry)

    async def _show_config_form(self, user_input):
        """Show the configuration form to edit configuration data."""

        data_schema = OrderedDict()
        data_schema[vol.Required(KEY_CMDR_NAME, default="")] = str
        data_schema[vol.Required(KEY_EDSM_API_KEY, default="", )] = str
        data_schema[vol.Required(KEY_INARA_API_KEY, default="")] = str

        if self.show_advanced_options:
            data_schema[vol.Optional(KEY_POP_SYSTEMS_REFRESH_INTERVAL, default=24)] = int

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data_schema),
            errors=self._errors,
        )

# TODO: test credentials

    # async def _test_credentials(self, username, password):
    #     """Return true if credentials is valid."""
    #     try:
    #         client = Client(username, password)
    #         await client.async_get_data()
    #         return True
    #     except Exception:  # pylint: disable=broad-except
    #         pass
    #     return False

# TODO: implement options flow

# class EDOptionsFlowHandler(config_entries.OptionsFlow):
#     """ED config flow options handler."""
#
#     def __init__(self, config_entry):
#         """Initialize HACS options flow."""
#         self.config_entry = config_entry
#         self.options = dict(config_entry.options)
#
#     async def async_step_init(self, user_input=None):
#         """Manage the options."""
#         return await self.async_step_user()
#
#     async def async_step_user(self, user_input=None):
#         """Handle a flow initialized by the user."""
#         if user_input is not None:
#             self.options.update(user_input)
#             return await self._update_options()
#
#         return self.async_show_form(
#             step_id="user",
#             data_schema=vol.Schema(
#                 {
#                     vol.Required(x, default=self.options.get(x, True)): bool
#                     for x in sorted(PLATFORMS)
#                 }
#             ),
#         )
#
#     async def _update_options(self):
#         """Update config entry options."""
#         return self.async_create_entry(
#             title=self.config_entry.data.get(CONF_USERNAME), data=self.options
#         )
