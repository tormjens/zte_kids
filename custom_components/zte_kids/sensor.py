"""Sensors (battery, steps, online, last fix) for each watch."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ZteKidsConfigEntry
from .const import DOMAIN
from .coordinator import ZteKidsCoordinator


@dataclass(frozen=True, kw_only=True)
class ZteKidsSensor(SensorEntityDescription):
    value: Callable[[dict], object]


def _fix_time(w: dict):
    ts = w.get("loc_time")
    return datetime.fromtimestamp(ts, tz=timezone.utc) if ts else None


SENSORS: tuple[ZteKidsSensor, ...] = (
    ZteKidsSensor(
        key="battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda w: w.get("battery"),
    ),
    ZteKidsSensor(
        key="steps",
        translation_key="steps",
        native_unit_of_measurement="steps",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value=lambda w: w.get("step_num"),
    ),
    ZteKidsSensor(
        key="last_fix",
        translation_key="last_fix",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=_fix_time,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZteKidsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        ZteKidsSensorEntity(coordinator, imei, desc)
        for imei in coordinator.data
        for desc in SENSORS
    )


class ZteKidsSensorEntity(CoordinatorEntity[ZteKidsCoordinator], SensorEntity):
    _attr_has_entity_name = True
    entity_description: ZteKidsSensor

    def __init__(
        self, coordinator: ZteKidsCoordinator, imei: str, desc: ZteKidsSensor
    ) -> None:
        super().__init__(coordinator)
        self._imei = imei
        self.entity_description = desc
        self._attr_unique_id = f"{imei}_{desc.key}"

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
    def native_value(self):
        return self.entity_description.value(self._watch)
