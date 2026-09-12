from __future__ import annotations

from typing import Any

import aiohttp

from .const import (
    API_BASE,
    DEFAULT_I18N,
    DEFAULT_PROJECT,
    DEFAULT_VW,
    LAST_DATA_ENDPOINT,
)


class ValueCloudsApiError(Exception):
    """Error communicating with ValueClouds."""


class ValueCloudsApi:
    """Simple client for ValueClouds."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        token: str,
        auth: str,
        sign: str,
        device_pn: str,
        device_sn: str,
        dev_code: str = "6422",
        dev_addr: str = "4",
    ) -> None:
        self.session = session
        self.token = token
        self.auth = auth
        self.sign = sign
        self.device_pn = device_pn
        self.device_sn = device_sn
        self.dev_code = dev_code
        self.dev_addr = dev_addr

    async def get_last_data(self) -> dict[str, Any]:
        """Get the latest inverter data."""

        headers = {
            "Accept": "application/json, text/plain, */*",
            "auth": self.auth,
            "token": self.token,
            "sign": self.sign,
            "project": DEFAULT_PROJECT,
            "i18n": DEFAULT_I18N,
            "vw": DEFAULT_VW,
        }

        params = {
            "devcode": self.dev_code,
            "pn": self.device_pn,
            "devaddr": self.dev_addr,
            "sn": self.device_sn,
            "i18n": DEFAULT_I18N,
        }

        try:
            async with self.session.get(
                f"{API_BASE}{LAST_DATA_ENDPOINT}",
                params=params,
                headers=headers,
            ) as response:
                response.raise_for_status()
                result = await response.json()

        except (aiohttp.ClientError, ValueError) as err:
            raise ValueCloudsApiError(
                f"Connection to ValueClouds failed: {err}"
            ) from err

        if result.get("code") != 0:
            raise ValueCloudsApiError(
                result.get("message")
                or result.get("errorMessage")
                or "ValueClouds returned an error"
            )

        return result
