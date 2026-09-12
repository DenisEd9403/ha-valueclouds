from __future__ import annotations

from typing import Any

import aiohttp

from .const import (
    API_BASE,
    DEFAULT_I18N,
    DEFAULT_PROJECT,
    DEFAULT_VW,
    LAST_DATA_ENDPOINT,
    LOGIN_ENDPOINT,
)


class ValueCloudsApiError(Exception):
    """ValueClouds API error."""


class ValueCloudsApi:
    """Simple ValueClouds API client."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        username: str,
        password: str,
        device_pn: str,
        device_sn: str,
        sign: str,
        dev_code: str = "6422",
        dev_addr: str = "4",
    ) -> None:
        self.session = session
        self.username = username
        self.password = password
        self.device_pn = device_pn
        self.device_sn = device_sn
        self.sign = sign
        self.dev_code = dev_code
        self.dev_addr = dev_addr

        self.token: str | None = None
        self.auth: str | None = None

    async def login(self) -> bool:
        """Login to ValueClouds."""

        payload = {
            "account": self.username,
            "password": self.password,
            "project": DEFAULT_PROJECT,
        }

        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "i18n": DEFAULT_I18N,
            "project": DEFAULT_PROJECT,
            "vw": DEFAULT_VW,
        }

        try:
            async with self.session.post(
                f"{API_BASE}{LOGIN_ENDPOINT}",
                json=payload,
                headers=headers,
            ) as response:
                response.raise_for_status()
                result = await response.json()

        except (aiohttp.ClientError, ValueError) as err:
            raise ValueCloudsApiError(
                f"Connection error: {err}"
            ) from err

        if result.get("code") != 0 or not result.get("success"):
            raise ValueCloudsApiError(
                result.get("message")
                or result.get("errorMessage")
                or "Login failed"
            )

        data = result.get("data") or {}

        self.token = data.get("token")

        if not self.token:
            raise ValueCloudsApiError(
                "ValueClouds did not return a token"
            )

        return True

    def set_auth(self, auth: str) -> None:
        """Set the ValueClouds auth JWT."""

        self.auth = auth

    def _headers(self) -> dict[str, str]:
        """Return authenticated request headers."""

        if not self.token:
            raise ValueCloudsApiError("Not authenticated")

        if not self.auth:
            raise ValueCloudsApiError("Auth token is missing")

        return {
            "Accept": "application/json, text/plain, */*",
            "auth": self.auth,
            "token": self.token,
            "sign": self.sign,
            "project": DEFAULT_PROJECT,
            "i18n": DEFAULT_I18N,
            "vw": DEFAULT_VW,
        }

    async def get_last_data(self) -> dict[str, Any]:
        """Get latest inverter data."""

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
                headers=self._headers(),
            ) as response:
                response.raise_for_status()
                result = await response.json()

        except (aiohttp.ClientError, ValueError) as err:
            raise ValueCloudsApiError(
                f"ValueClouds request failed: {err}"
            ) from err

        if result.get("code") != 0:
            raise ValueCloudsApiError(
                result.get("message")
                or result.get("errorMessage")
                or "ValueClouds returned an error"
            )

        return result
