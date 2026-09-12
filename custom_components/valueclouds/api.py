from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
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
    """Client for the ValueClouds API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        username: str,
        password: str,
        device_pn: str,
        device_sn: str,
        dev_code: str = "6422",
        dev_addr: str = "4",
    ) -> None:
        self.session = session
        self.username = username
        self.password = password
        self.device_pn = device_pn
        self.device_sn = device_sn
        self.dev_code = dev_code
        self.dev_addr = dev_addr

        self.token: str | None = None
        self.secret: str | None = None
        self.auth: str | None = None
        self.sign: str | None = None

    @staticmethod
    def _sha1(value: str) -> str:
        """Return SHA-1 hexadecimal digest."""
        return hashlib.sha1(value.encode("utf-8")).hexdigest()

    @staticmethod
    def _base64url(data: bytes) -> str:
        """Base64 URL encoding without padding."""
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

    def _create_auth(self, user_id: int) -> str:
        """Create the JWT used by ValueClouds requests."""

        header = {
            "alg": "HS256",
            "typ": "JWT",
        }

        now = int(time.time())

        payload = {
            "jti": str(user_id),
            "sub": f"User{user_id}",
            "iss": "EYBOND",
            "iat": now,
            "Auth": "[]",
            "Auth_all": "[]",
        }

        header_part = self._base64url(
            json.dumps(
                header,
                separators=(",", ":"),
            ).encode("utf-8")
        )

        payload_part = self._base64url(
            json.dumps(
                payload,
                separators=(",", ":"),
            ).encode("utf-8")
        )

        unsigned = f"{header_part}.{payload_part}"

        signature = hmac.new(
            self.secret.encode("utf-8"),
            unsigned.encode("ascii"),
            hashlib.sha256,
        ).digest()

        return f"{unsigned}.{self._base64url(signature)}"

    async def login(self) -> bool:
        """Authenticate against ValueClouds."""

        payload = {
            "account": self.username,
            "password": self._sha1(self.password),
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
        self.secret = data.get("secret")

        user_id = data.get("userId")

        if not self.token:
            raise ValueCloudsApiError(
                "ValueClouds did not return a token"
            )

        if not self.secret:
            raise ValueCloudsApiError(
                "ValueClouds did not return a secret"
            )

        if not user_id:
            raise ValueCloudsApiError(
                "ValueClouds did not return a user ID"
            )

        self.auth = self._create_auth(int(user_id))

        # ValueClouds uses a 64-character hexadecimal signature.
        # The current API uses the SHA-256 digest of the session secret.
        self.sign = hashlib.sha256(
            self.secret.encode("utf-8")
        ).hexdigest()

        return True

    def _headers(self) -> dict[str, str]:
        """Build authenticated request headers."""

        if not self.token or not self.auth or not self.sign:
            raise ValueCloudsApiError("Not authenticated")

        return {
            "Accept": "application/json, text/plain, */*",
            "auth": self.auth,
            "token": self.token,
            "sign": self.sign,
            "project": DEFAULT_PROJECT,
            "i18n": DEFAULT_I18N,
            "vw": DEFAULT_VW,
        }

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
        """Get latest inverter data."""

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
        """Get current energy flow."""

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
