"""巴法云空调设备平台."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
    FAN_AUTO,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
    SWING_OFF,
    SWING_BOTH,
    SWING_HORIZONTAL,
    SWING_VERTICAL,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    UnitOfTemperature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_API_KEY,
    MSG_ON,
    MSG_OFF,
    MSG_SEPARATOR,
)
from .helpers import BemfaBaseEntity

_LOGGER = logging.getLogger(__name__)

# 空调模式映射
HVAC_MODES = {
    "1": HVACMode.AUTO,
    "2": HVACMode.COOL,
    "3": HVACMode.HEAT,
    "4": HVACMode.FAN_ONLY,
    "5": HVACMode.DRY,
}
HVAC_MODES_REVERSE = {v: k for k, v in HVAC_MODES.items()}

# 风速映射
FAN_MODES = {
    "0": FAN_AUTO,
    "1": FAN_LOW,
    "2": FAN_MEDIUM,
    "3": FAN_HIGH,
}
FAN_MODES_REVERSE = {v: k for k, v in FAN_MODES.items()}

# 扫风映射
SWING_MODES = {
    "0#0": SWING_OFF,
    "1#0": SWING_HORIZONTAL,
    "0#1": SWING_VERTICAL,
    "1#1": SWING_BOTH,
}
SWING_MODES_REVERSE = {v: k for k, v in SWING_MODES.items()}

# 温度范围
MIN_TEMP = 16
MAX_TEMP = 32

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置巴法云空调设备."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    mqtt_client = hass.data[DOMAIN][entry.entry_id]["mqtt_client"]
    
    entities = [
        BemfaClimate(coordinator, mqtt_client, topic, entry)
        for topic, device in coordinator.data.items()
        if device["type"] == "climate"
    ]
    
    if entities:
        async_add_entities(entities)

class BemfaClimate(CoordinatorEntity, BemfaBaseEntity, ClimateEntity):
    """巴法云空调设备."""

    _attr_has_entity_name = True
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF] + list(HVAC_MODES.values())
    _attr_fan_modes = list(FAN_MODES.values())
    _attr_swing_modes = list(SWING_MODES.values())
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP
    _attr_target_temperature_step = 1
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE |
        ClimateEntityFeature.FAN_MODE |
        ClimateEntityFeature.SWING_MODE
    )

    def __init__(self, coordinator, mqtt_client, topic, entry):
        """初始化巴法云空调设备."""
        super().__init__(coordinator)
        BemfaBaseEntity.__init__(self, topic, coordinator.data[topic]["name"])
        
        self._topic = topic
        self._mqtt_client = mqtt_client
        self._api_key = entry.data[CONF_API_KEY]
        self._attr_unique_id = f"{DOMAIN}_{topic}_climate"
        self._attr_name = "空调"
        
        self._parse_state(coordinator.data[topic].get("state", ""))

    def _parse_state(self, state: str) -> None:
        """解析设备状态."""
        if not state:
            self._attr_hvac_mode = HVACMode.OFF
            self._attr_target_temperature = MIN_TEMP
            self._attr_fan_mode = FAN_AUTO
            self._attr_swing_mode = SWING_OFF
            return

        parts = state.split(MSG_SEPARATOR)
        self._attr_hvac_mode = HVACMode.OFF if parts[0].lower() != MSG_ON else HVACMode.AUTO
        
        if len(parts) > 1 and self._attr_hvac_mode != HVACMode.OFF:
            self._attr_hvac_mode = HVAC_MODES.get(parts[1], HVACMode.AUTO)
        
        if len(parts) > 2 and self._attr_hvac_mode != HVACMode.OFF:
            try:
                self._attr_target_temperature = float(parts[2])
            except (ValueError, IndexError):
                self._attr_target_temperature = MIN_TEMP
        
        if len(parts) > 3 and self._attr_hvac_mode != HVACMode.OFF:
            self._attr_fan_mode = FAN_MODES.get(parts[3], FAN_AUTO)
        
        if len(parts) > 5 and self._attr_hvac_mode != HVACMode.OFF:
            try:
                swing_key = f"{parts[4]}#{parts[5]}"
                self._attr_swing_mode = SWING_MODES.get(swing_key, SWING_OFF)
            except (ValueError, IndexError):
                self._attr_swing_mode = SWING_OFF

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """设置温度."""
        if ATTR_TEMPERATURE in kwargs:
            temperature = kwargs[ATTR_TEMPERATURE]
            await self._async_update_state(temperature=temperature)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """设置空调模式."""
        if hvac_mode == HVACMode.OFF:
            await self._async_send_command(MSG_OFF)
        else:
            await self._async_update_state(hvac_mode=hvac_mode)

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """设置风速."""
        await self._async_update_state(fan_mode=fan_mode)

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """设置扫风模式."""
        await self._async_update_state(swing_mode=swing_mode)

    async def _async_update_state(
        self,
        temperature: float | None = None,
        hvac_mode: HVACMode | None = None,
        fan_mode: str | None = None,
        swing_mode: str | None = None,
    ) -> None:
        """更新设备状态."""
        if hvac_mode is None:
            hvac_mode = self.hvac_mode
        if temperature is None:
            temperature = self.target_temperature
        if fan_mode is None:
            fan_mode = self.fan_mode
        if swing_mode is None:
            swing_mode = self.swing_mode

        if hvac_mode == HVACMode.OFF:
            await self._async_send_command(MSG_OFF)
            return

        mode = HVAC_MODES_REVERSE.get(hvac_mode, "1")
        temp = int(max(MIN_TEMP, min(MAX_TEMP, temperature)))
        fan = FAN_MODES_REVERSE.get(fan_mode, "0")
        swing = SWING_MODES_REVERSE.get(swing_mode, "0#0")
        
        msg = f"{MSG_ON}#{mode}#{temp}#{fan}#{swing}"
        await self._async_send_command(msg)

    async def _async_send_command(self, command: str) -> None:
        """发送命令到巴法云."""
        try:
            self._mqtt_client.publish(f"{self._topic}/set", command)
            self._parse_state(command)
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        except Exception as ex:
            _LOGGER.error("发送命令失败: %s", ex)

    @property
    def available(self) -> bool:
        """返回设备是否可用."""
        return self.coordinator.data.get(self._topic, {}).get("online", True)

    def _handle_coordinator_update(self) -> None:
        """处理设备状态更新."""
        device = self.coordinator.data.get(self._topic, {})
        self._parse_state(device.get("state", ""))
        self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)