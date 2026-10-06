"""Config flow for ZTE Kids Watch."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ZteKidsApiError, ZteKidsAuthError, ZteKidsClient
from .const import DOMAIN

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required("login_name"): str,
        vol.Required("password"): str,
    }
)


class ZteKidsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the login form."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            client = ZteKidsClient(
                async_get_clientsession(self.hass),
                user_input["login_name"],
                user_input["password"],
            )
            try:
                await client.async_validate()
            except ZteKidsAuthError:
                errors["base"] = "invalid_auth"
            except ZteKidsApiError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(user_input["login_name"].lower())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"ZTE Kids ({user_input['login_name']})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )
