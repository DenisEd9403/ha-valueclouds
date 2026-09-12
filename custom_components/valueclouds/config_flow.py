from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import aiohttp_client

from .api import ValueCloudsApi, ValueCloudsApiError
from .const import (
    CONF_AUTH,
    CONF_DEVICE_PN,
    CONF_DEVICE_SN,
    CONF_SIGN,
    CONF_TOKEN,
    DOMAIN,
)


class ValueCloudsConfigFlow(
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    """Handle ValueClouds configuration."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Handle the setup form."""

        errors: dict[str, str] = {}

        if user_input is not None:
            session = aiohttp_client.async_get_clientsession(self.hass)

            api = ValueCloudsApi(
                session=session,
                token=user_input[CONF_TOKEN],
                auth=user_input[CONF_AUTH],
                sign=user_input[CONF_SIGN],
                device_pn=user_input[CONF_DEVICE_PN],
                device_sn=user_input[CONF_DEVICE_SN],
            )

            try:
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
                vol.Required(CONF_TOKEN): str,
                vol.Required(CONF_AUTH): str,
                vol.Required(CONF_SIGN): str,
                vol.Required(CONF_DEVICE_PN): str,
                vol.Required(CONF_DEVICE_SN): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
