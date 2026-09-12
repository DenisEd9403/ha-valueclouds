from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import ValueCloudsApi, ValueCloudsApiError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN


class ValueCloudsCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for ValueClouds data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: ValueCloudsApi,
    ) -> None:
        self.api = api

        super().__init__(
            hass,
            logger=__import__("logging").getLogger(DOMAIN),
            name="ValueClouds",
            update_interval=timedelta(
                seconds=DEFAULT_SCAN_INTERVAL
            ),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from ValueClouds."""

        try:
            result = await self.api.get_last_data()

        except ValueCloudsApiError as err:
            raise UpdateFailed(str(err)) from err

        return result
