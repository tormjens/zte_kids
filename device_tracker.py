"""Device tracker (map location) for each watch."""
from __future__ import annotations

from homeassistant.components.device_tracker import SourceType, TrackerEntity
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
        ZteKidsTracker(coordinator, imei) for imei in coordinator.data
    )


class ZteKidsTracker(CoordinatorEntity[ZteKidsCoordinator], TrackerEntity):
    _attr_has_entity_name = True
    _attr_name = None  # the device name is the watch name

    def __init__(self, coordinator: ZteKidsCoordinator, imei: str) -> None:
        super().__init__(coordinator)
        self._imei = imei
        self._attr_unique_id = f"{imei}_tracker"

    @property
    def _watch(self) -> dict:
        return self.coordinator.data.get(self._imei, {})

    @property
    def device_info(self) -> DeviceInfo:
        w = self._watch
        return DeviceInfo(
            identifiers={(DOMAIN, self._imei)},
            name=w.get("name") or self._imei,
            manufacturer="ZTE / nubia",
            model=w.get("model"),
        )

    @property
    def source_type(self) -> SourceType:
        return SourceType.GPS

    @property
    def latitude(self) -> float | None:
        return self._watch.get("lat")

    @property
    def longitude(self) -> float | None:
        return self._watch.get("lon")

    @property
    def location_accuracy(self) -> int:
        return int(self._watch.get("accuracy") or 0)

    @property
    def extra_state_attributes(self) -> dict:
        w = self._watch
        return {
            "address": w.get("address"),
            "loc_type": w.get("loc_type"),
            "loc_time": w.get("loc_time"),
            "online": w.get("online"),
        }
