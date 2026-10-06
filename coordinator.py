"""DataUpdateCoordinator for ZTE Kids Watch."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ZteKidsApiError, ZteKidsAuthError, ZteKidsClient
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class ZteKidsCoordinator(DataUpdateCoordinator[dict[str, dict]]):
    """Polls the account and exposes {imei: watch_state}."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.entry = entry
        self.client = ZteKidsClient(
            async_get_clientsession(hass),
            entry.data["login_name"],
            entry.data["password"],
        )

    async def _async_update_data(self) -> dict[str, dict]:
        try:
            watches = await self.client.async_get_watches()
        except ZteKidsAuthError as err:
            # Credentials no longer valid -> trigger reauth in HA.
            from homeassistant.exceptions import ConfigEntryAuthFailed

            raise ConfigEntryAuthFailed(str(err)) from err
        except ZteKidsApiError as err:
            raise UpdateFailed(str(err)) from err
        return {w["imei"]: w for w in watches if w.get("imei")}
