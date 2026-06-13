from typing import Callable, Awaitable
from dataclasses import dataclass

from homeassistant.core import HomeAssistant
from homeassistant.components.select import SelectEntity, SelectEntityDescription

from .const import DOMAIN, DATA_COORDINATORS, SELECT_HORIZONTAL_SWING, SELECT_VERTICAL_SWING, AQUAREA_COORDINATORS
from aio_panasonic_comfort_cloud import PanasonicDevice, ChangeRequestBuilder, constants
from aioaquarea import Device as AquareaDevice
from aioaquarea.data import QuietMode

from .coordinator import PanasonicDeviceCoordinator, AquareaDeviceCoordinator
from .base import PanasonicDataEntity, AquareaDataEntity

@dataclass(frozen=True, kw_only=True)
class PanasonicSelectEntityDescription(SelectEntityDescription):
    """Description of a select entity."""
    set_option: Callable[[ChangeRequestBuilder, str], ChangeRequestBuilder]
    get_current_option: Callable[[PanasonicDevice], str]
    is_available: Callable[[PanasonicDevice], bool]
    get_options: Callable[[PanasonicDevice], list[str]] = None


HORIZONTAL_SWING_DESCRIPTION = PanasonicSelectEntityDescription(
    key=SELECT_HORIZONTAL_SWING, 
    translation_key=SELECT_HORIZONTAL_SWING,
    icon="mdi:swap-horizontal",
    name="Horizontal Swing Mode",
    options= [opt.name for opt in constants.AirSwingLR if opt != constants.AirSwingLR.Unavailable],
    set_option = lambda builder, new_value : builder.set_horizontal_swing(new_value),
    get_current_option = lambda device : device.parameters.horizontal_swing_mode.name,
    is_available = lambda device : device.has_horizontal_swing
)
VERTICAL_SWING_DESCRIPTION = PanasonicSelectEntityDescription(
    key=SELECT_VERTICAL_SWING, 
    translation_key=SELECT_VERTICAL_SWING,
    icon="mdi:swap-vertical",
    name="Vertical Swing Mode",
    get_options= lambda device: [opt.name for opt in constants.AirSwingUD if opt != constants.AirSwingUD.Swing or device.features.auto_swing_ud],
    set_option = lambda builder, new_value : builder.set_vertical_swing(new_value),
    get_current_option = lambda device : device.parameters.vertical_swing_mode.name,
    is_available = lambda device : True
)


@dataclass(frozen=True, kw_only=True)
class AquareaSelectEntityDescription(SelectEntityDescription):
    """Description of an Aquarea select entity."""
    options: list[str] = None
    get_current_option: Callable[[AquareaDevice], str] = None
    set_option: Callable[[AquareaDevice, str], Awaitable] = None


AQUAREA_QUIET_MODE_DESCRIPTION = AquareaSelectEntityDescription(
    key="quiet_mode",
    name="Quiet Mode",
    icon="mdi:volume-off",
    options=[q.name.lower() for q in QuietMode],
    get_current_option=lambda device: device.quiet_mode.name.lower() if device.quiet_mode is not None else QuietMode.OFF.name.lower(),
    set_option=lambda device, option: device.set_quiet_mode(QuietMode[option.upper()]),
)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    entities = []
    data_coordinators: list[PanasonicDeviceCoordinator] = hass.data[DOMAIN][DATA_COORDINATORS]
    aquarea_coordinators: list[AquareaDeviceCoordinator] = hass.data[DOMAIN][AQUAREA_COORDINATORS]
    for coordinator in data_coordinators:
        entities.append(PanasonicSelectEntity(coordinator, HORIZONTAL_SWING_DESCRIPTION))
        entities.append(PanasonicSelectEntity(coordinator, VERTICAL_SWING_DESCRIPTION))
    for coordinator in aquarea_coordinators:
        entities.append(AquareaSelectEntity(coordinator, AQUAREA_QUIET_MODE_DESCRIPTION))

    async_add_entities(entities)

class PanasonicSelectEntityBase(SelectEntity):
    """Base class for all select entities."""
    entity_description: PanasonicSelectEntityDescription

class PanasonicSelectEntity(PanasonicDataEntity, PanasonicSelectEntityBase):

    def __init__(self, coordinator: PanasonicDeviceCoordinator, description: PanasonicSelectEntityDescription):
        self.entity_description = description
        if description.get_options is not None:
            self._attr_options = description.get_options(coordinator.device)
        super().__init__(coordinator, description.key)
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.entity_description.is_available(self.coordinator.device)

    async def async_select_option(self, option: str) -> None:
        builder = self.coordinator.get_change_request_builder()
        self.entity_description.set_option(builder, option)
        await self.coordinator.async_apply_changes(builder)
        self._attr_current_option = option
        self.async_write_ha_state()

    def _async_update_attrs(self) -> None:
        self.current_option = self.entity_description.get_current_option(self.coordinator.device)


class AquareaSelectEntity(AquareaDataEntity, SelectEntity):
    """Aquarea select entity (e.g. quiet mode)."""

    entity_description: AquareaSelectEntityDescription

    def __init__(self, coordinator: AquareaDeviceCoordinator, description: AquareaSelectEntityDescription):
        self.entity_description = description
        self._attr_options = description.options
        super().__init__(coordinator, description.key)

    def _async_update_attrs(self) -> None:
        self._attr_current_option = self.entity_description.get_current_option(self.coordinator.device)

    async def async_select_option(self, option: str) -> None:
        await self.entity_description.set_option(self.coordinator.device, option)
        self._attr_current_option = option
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

