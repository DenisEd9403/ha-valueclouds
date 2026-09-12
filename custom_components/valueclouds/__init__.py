from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client

from .api import ValueCloudsApi
from .const import (
    CONF_AUTH,
    CONF_DEVICE_PN,
    CONF_DEVICE_SN,
    CONF_SIGN,
    CONF_TOKEN,
    DOMAIN,
)
from .coordinator import ValueCloudsCoordinator


PLATFORMS = ["sensor"]


async def async_setup(
    hass: HomeAssistant,
    config: dict,
) -> bool:
    """Set up ValueClouds."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up ValueClouds from a config entry."""

    session = aiohttp_client.async_get_clientsession(hass)

    api = ValueCloudsApi(
        session=session,
        token=entry.data[CONF_TOKEN],
        auth=entry.data[CONF_AUTH],
        sign=entry.data[CONF_SIGN],
        device_pn=entry.data[CONF_DEVICE_PN],
        device_sn=entry.data[CONF_DEVICE_SN],
    )

    coordinator = ValueCloudsCoordinator(
        hass,
        api,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload ValueClouds."""

    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
