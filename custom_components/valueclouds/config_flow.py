from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from .api import ValueCloudsApi, ValueCloudsApiError
from .const import (
    CONF_DEVICE_PN,
    CONF_DEVICE_SN,
    DEFAULT_DEV_ADDR,
    DEFAULT_DEV_CODE,
    DOMAIN,
)


class ValueCloudsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a ValueClouds config flow."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Handle the user setup step."""

        errors: dict[str, str] = {}

        if user_input is not None:
            api = ValueCloudsApi(
                self.hass.helpers.aiohttp_client.async_get_clientsession(),
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
                device_pn=user_input[CONF_DEVICE_PN],
                device_sn=user_input[CONF_DEVICE_SN],
                dev_code=DEFAULT_DEV_CODE,
                dev_addr=DEFAULT_DEV_ADDR,
            )

            try:
                await api.login()
                await api.get_last_data()

            except ValueCloudsApiError:
                errors["base"] = "cannot_connect"

            else:
                await self.async_set_unique_id(
                    user_input[CONF_DEVICE_SN]
                )
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"ValueClouds {user_input[CONF_DEVICE_SN]}",
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): vol.All(
                    str,
                    vol.Length(min=1),
                ),
                vol.Required(CONF_DEVICE_PN): str,
                vol.Required(CONF_DEVICE_SN): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
