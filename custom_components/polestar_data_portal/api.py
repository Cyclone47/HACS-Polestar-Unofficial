"""API client for the official Polestar Data Portal M2M API."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import logging
import time
from typing import Any

import aiohttp

from .const import (
    BASE_URL,
    CHARGING_ENDPOINTS,
    TELEMETRY_ENDPOINTS,
    TOKEN_URL,
    VEHICLES_URL,
)

_LOGGER = logging.getLogger(__name__)


class PolestarApiError(Exception):
    """General Polestar API error."""


class PolestarAuthError(PolestarApiError):
    """Authentication or authorization error."""


class PolestarConnectionError(PolestarApiError):
    """Connection or server error."""


class PolestarRateLimitError(PolestarApiError):
    """API rate limit exceeded."""


class PolestarApiClient:
    """Polestar Data Portal M2M API Client."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        account_id: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize the API client."""
        self._client_id = client_id.strip()
        self._client_secret = client_secret.strip()
        self._account_id = account_id.strip()
        self._session = session

        self._access_token: str | None = None
        self._token_expires_at: float = 0.0
        self._lock = asyncio.Lock()

    async def async_get_access_token(self, force_refresh: bool = False) -> str:
        """Get or refresh the OAuth2 Bearer token."""
        async with self._lock:
            now = time.time()
            # Token is valid if expiration is at least 60 seconds in the future
            if not force_refresh and self._access_token and now < (self._token_expires_at - 60):
                return self._access_token

            payload = {
                "clientId": self._client_id,
                "clientSecret": self._client_secret,
            }
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            try:
                async with self._session.post(
                    TOKEN_URL, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=20)
                ) as resp:
                    if resp.status in (400, 401, 403):
                        error_text = await resp.text()
                        _LOGGER.error("Polestar token authentication failed (status %d): %s", resp.status, error_text)
                        raise PolestarAuthError(f"Authentication failed: HTTP {resp.status} - {error_text}")

                    if resp.status == 429:
                        raise PolestarRateLimitError("Token endpoint rate limit reached.")

                    if resp.status >= 500:
                        error_text = await resp.text()
                        raise PolestarConnectionError(f"Polestar token server error {resp.status}: {error_text}")

                    data = await resp.json()
                    access_token = data.get("accessToken")
                    expires_in = data.get("expiresIn", 3600)

                    if not access_token:
                        raise PolestarAuthError("Token response did not contain an accessToken.")

                    self._access_token = access_token
                    self._token_expires_at = now + expires_in
                    _LOGGER.debug("Acquired Polestar M2M token, valid for %d seconds", expires_in)
                    return access_token

            except aiohttp.ClientError as err:
                _LOGGER.error("Network error requesting Polestar token: %s", err)
                raise PolestarConnectionError(f"Network error connecting to Polestar: {err}") from err

    async def _async_request(
        self,
        method: str,
        url: str,
        retry_auth: bool = True,
    ) -> Any:
        """Perform an authenticated HTTP request with token retry."""
        token = await self.async_get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "x-client-id": self._account_id,
            "Accept": "application/json",
        }

        try:
            async with self._session.request(
                method, url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)
            ) as resp:
                # Handle unauthorized or forbidden by refreshing token once
                if resp.status in (401, 403) and retry_auth:
                    _LOGGER.debug("Polestar API returned %d, refreshing token and retrying", resp.status)
                    token = await self.async_get_access_token(force_refresh=True)
                    headers["Authorization"] = f"Bearer {token}"
                    async with self._session.request(
                        method, url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)
                    ) as retry_resp:
                        return await self._handle_response(retry_resp, url)

                return await self._handle_response(resp, url)

        except aiohttp.ClientError as err:
            _LOGGER.warning("Connection error to %s: %s", url, err)
            raise PolestarConnectionError(f"Connection error to {url}: {err}") from err

    async def _handle_response(self, resp: aiohttp.ClientResponse, url: str) -> Any:
        """Handle HTTP response status and parse body."""
        if resp.status == 200:
            return await resp.json()

        if resp.status == 404:
            # 404 commonly means DATA_NOT_AVAILABLE for an optional domain on this car model
            try:
                json_data = await resp.json()
                error_code = json_data.get("error", {}).get("code")
                _LOGGER.debug("Endpoint %s returned 404 (code: %s)", url, error_code)
            except Exception:
                _LOGGER.debug("Endpoint %s returned 404 Not Found", url)
            return None

        if resp.status == 429:
            _LOGGER.warning("Polestar API rate limit (10,000/day or 100/min) exceeded for %s", url)
            raise PolestarRateLimitError(f"Rate limit exceeded on {url}")

        if resp.status in (401, 403):
            err_text = await resp.text()
            _LOGGER.error("Polestar authorization failure (%d) for %s: %s", resp.status, url, err_text)
            raise PolestarAuthError(f"Authorization failed on {url}: HTTP {resp.status} - {err_text}")

        if resp.status >= 500:
            err_text = await resp.text()
            _LOGGER.warning("Polestar server error (%d) for %s: %s", resp.status, url, err_text)
            raise PolestarConnectionError(f"Polestar server error {resp.status} on {url}: {err_text}")

        err_text = await resp.text()
        raise PolestarApiError(f"Unexpected response ({resp.status}) from {url}: {err_text}")

    async def async_get_vehicles(self) -> list[str]:
        """Fetch list of authorized vehicle VINs."""
        resp_json = await self._async_request("GET", VEHICLES_URL)
        if not resp_json:
            return []
        vehicles = resp_json.get("data", [])
        _LOGGER.debug("Fetched authorized Polestar vehicles: %s", vehicles)
        return vehicles

    async def async_get_endpoint(self, vin: str, path: str) -> dict[str, Any] | None:
        """Fetch a single telemetry or charging endpoint for a VIN."""
        url = f"{BASE_URL}/v1/vehicles/{vin}/{path}"
        resp_json = await self._async_request("GET", url)
        if not resp_json:
            return None
        return resp_json.get("data")

    async def async_get_all_telemetry(self, vin: str) -> dict[str, Any]:
        """Fetch all telemetry and charging endpoints in parallel."""
        all_endpoints: dict[str, str] = {**TELEMETRY_ENDPOINTS, **CHARGING_ENDPOINTS}
        keys = list(all_endpoints.keys())

        tasks = [
            self.async_get_endpoint(vin, all_endpoints[key])
            for key in keys
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        data: dict[str, Any] = {
            "vin": vin,
            "meta_last_updated": datetime.now(timezone.utc).isoformat(),
        }

        for key, res in zip(keys, results):
            if isinstance(res, Exception):
                _LOGGER.debug("Error fetching Polestar domain '%s' for %s: %s", key, vin, res)
                data[key] = None
            else:
                data[key] = res

        return data
