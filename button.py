"""Button to request a fresh GPS fix from a watch."""
from __future__ import annotations

import asyncio

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ZteKidsConfigEntry
from .const import DOMAIN
from .coordinator import ZteKidsCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZteKidsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        ZteKidsRefreshButton(coordinator, imei) for imei in coordinator.data
    )


class ZteKidsRefreshButton(CoordinatorEntity[ZteKidsCoordinator], ButtonEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "refresh_location"
    _attr_icon = "mdi:crosshairs-gps"

    def __init__(self, coordinator: ZteKidsCoordinator, imei: str) -> None:
        super().__init__(coordinator)
        self._imei = imei
        self._attr_unique_id = f"{imei}_refresh_location"

    @property
    def device_info(self) -> DeviceInfo:
        w = self.coordinator.data.get(self._imei, {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._imei)},
            name=w.get("name") or self._imei,
            manufacturer="ZTE / nubia",
            model=w.get("model"),
        )

    async def async_press(self) -> None:
        await self.coordinator.client.async_request_location(self._imei)
        # Give the watch a moment to report, then re-poll so the new fix shows up.
        await asyncio.sleep(8)
        await self.coordinator.async_request_refresh()
