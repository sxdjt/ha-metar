"""Base entity class shared across METAR platforms."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import MetarCoordinator


class MetarEntity(CoordinatorEntity[MetarCoordinator]):
    """Base class for all METAR entities.

    Handles the device registration and attribution that is common to every
    entity created by this integration.
    """

    _attr_attribution = ATTRIBUTION
    # has_entity_name=True: HA prepends the device name ("EGLL") to the entity
    # name ("QNH") automatically, giving display name "EGLL QNH".
    # suggested_object_id on MetarSensor controls the entity ID independently.
    _attr_has_entity_name = True

    def __init__(self, coordinator: MetarCoordinator) -> None:
        """Initialize the base entity."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.station_id)},
            name=f"METAR {coordinator.station_id}",
            manufacturer="Aviation Weather Center",
            model="METAR",
            entry_type=DeviceEntryType.SERVICE,
        )
