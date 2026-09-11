from __future__ import annotations

import hashlib
from typing import Any

import aiohttp

from .const import (
    API_BASE,
    DEFAULT_I18N,
    DEFAULT_PROJECT,
    DEFAULT_VW,
    ENERGY_FLOW_ENDPOINT,
    LAST_DATA_ENDPOINT,
    LOGIN_ENDPOINT,
)


class ValueCloudsApiError(Exception):
    """Error communicating with ValueClouds."""


class ValueCloudsApi:
    """Client for the ValueClouds cloud API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        username: str,
        password: str,
        device_pn: str,
        device_sn: str,
        dev_code: str = "6422",
        dev_addr: str = "4",
        sign: str = "",
    ) -> None:
        self.session = session
        self.username = username
        self.password = password
        self.device_pn = device_pn
        self.device_sn = device_sn
        self.dev_code = dev_code
        self.dev_addr = dev_addr
        self.sign = sign

        self.token: str | None = None
        self.auth: str | None = None

    @staticmethod
    def _password_hash(password: str) -> str:
        """ValueClouds sends the password as a SHA-1 hexadecimal string."""
        return hashlib.sha1(password.encode("utf-8")).hexdigest()

    async def login(self) -> bool:
        """Authenticate against ValueClouds."""

        payload = {
            "account": self.username,
            "password": self._password_hash(self.password),
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
                f"Unable to connect to ValueClouds: {err}"
            ) from err

        if result.get("code") != 0 or not result.get("success"):
            raise ValueCloudsApiError(
                result.get("message")
                or result.get("errorMessage")
                or "ValueClouds login failed"
            )

        data = result.get("data") or {}

        self.token = data.get("token")
        self.auth = data.get("auth")

        if not self.token:
            raise ValueCloudsApiError("ValueClouds did not return a token")

        return True

    def _headers(self) -> dict[str, str]:
        """Build headers required by authenticated ValueClouds requests."""

        if not self.token:
            raise ValueCloudsApiError("Not authenticated")

        headers = {
            "Accept": "application/json, text/plain, */*",
            "i18n": DEFAULT_I18N,
            "project": DEFAULT_PROJECT,
            "vw": DEFAULT_VW,
            "token": self.token,
        }

        if self.auth:
            headers["auth"] = self.auth

        if self.sign:
            headers["sign"] = self.sign

        return headers

    async def _get(
        self,
        endpoint: str,
        params: dict[str, str],
    ) -> dict[str, Any]:
        """Perform an authenticated GET request."""

        try:
            async with self.session.get(
                f"{API_BASE}{endpoint}",
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

    async def get_last_data(self) -> dict[str, Any]:
        """Get the latest inverter data."""

        return await self._get(
            LAST_DATA_ENDPOINT,
            {
                "devcode": self.dev_code,
                "pn": self.device_pn,
                "devaddr": self.dev_addr,
                "sn": self.device_sn,
                "i18n": DEFAULT_I18N,
            },
        )

    async def get_energy_flow(self) -> dict[str, Any]:
        """Get the current energy flow."""

        return await self._get(
            ENERGY_FLOW_ENDPOINT,
            {
                "devcode": self.dev_code,
                "pn": self.device_pn,
                "devaddr": self.dev_addr,
                "sn": self.device_sn,
                "i18n": DEFAULT_I18N,
            },
        )
