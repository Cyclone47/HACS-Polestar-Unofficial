"""Config flow for Polestar Data Portal integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    PolestarApiClient,
    PolestarAuthError,
    PolestarConnectionError,
    PolestarRateLimitError,
)
from .const import (
    CONF_ACCOUNT_ID,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_SCAN_INTERVAL,
    CONF_VIN,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CLIENT_ID): str,
        vol.Required(CONF_CLIENT_SECRET): str,
        vol.Required(CONF_ACCOUNT_ID): str,
    }
)


class PolestarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Polestar Data Portal."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._user_input: dict[str, Any] = {}
        self._vehicles: list[str] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial user credentials step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            api = PolestarApiClient(
                client_id=user_input[CONF_CLIENT_ID],
                client_secret=user_input[CONF_CLIENT_SECRET],
                account_id=user_input[CONF_ACCOUNT_ID],
                session=session,
            )

            try:
                vehicles = await api.async_get_vehicles()
            except PolestarAuthError:
                errors["base"] = "invalid_auth"
            except PolestarRateLimitError:
                errors["base"] = "rate_limited"
            except PolestarConnectionError:
                errors["base"] = "cannot_connect"
            except Exception as err:
                _LOGGER.exception("Unexpected exception during Polestar setup: %s", err)
                errors["base"] = "unknown"
            else:
                if not vehicles:
                    errors["base"] = "no_vehicles"
                elif len(vehicles) == 1:
                    vin = vehicles[0]
                    await self.async_set_unique_id(vin)
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=f"Polestar ({vin})",
                        data={
                            CONF_CLIENT_ID: user_input[CONF_CLIENT_ID].strip(),
                            CONF_CLIENT_SECRET: user_input[CONF_CLIENT_SECRET].strip(),
                            CONF_ACCOUNT_ID: user_input[CONF_ACCOUNT_ID].strip(),
                            CONF_VIN: vin,
                        },
                    )
                else:
                    self._user_input = {
                        CONF_CLIENT_ID: user_input[CONF_CLIENT_ID].strip(),
                        CONF_CLIENT_SECRET: user_input[CONF_CLIENT_SECRET].strip(),
                        CONF_ACCOUNT_ID: user_input[CONF_ACCOUNT_ID].strip(),
                    }
                    self._vehicles = vehicles
                    return await self.async_step_vehicle()

        return self.async_show_form(
            step_id="user",
            data_schema=USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_vehicle(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle vehicle selection step if multiple VINs are authorized."""
        errors: dict[str, str] = {}

        if user_input is not None:
            vin = user_input[CONF_VIN]
            await self.async_set_unique_id(vin)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Polestar ({vin})",
                data={
                    **self._user_input,
                    CONF_VIN: vin,
                },
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_VIN, default=self._vehicles[0]): vol.In(self._vehicles),
            }
        )

        return self.async_show_form(
            step_id="vehicle",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow handler."""
        return PolestarOptionsFlowHandler(config_entry)


class PolestarOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Polestar Data Portal."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage Polestar options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )

        options_schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=current_interval,
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
        )
