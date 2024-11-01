"""巴法云灯光设备平台."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.color import (
    color_temperature_kelvin_to_mired,
    color_temperature_mired_to_kelvin,
)

from .const import (
    DOMAIN,
    CONF_API_KEY,
    MSG_SEPARATOR,
)
from .helpers import BemfaBaseEntity

_LOGGER = logging.getLogger(__name__)

# 色温范围（开尔文）
MIN_KELVIN = 2700  # 暖光
MAX_KELVIN = 6500  # 冷光

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置巴法云灯光设备."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    mqtt_client = hass.data[DOMAIN][entry.entry_id]["mqtt_client"]
    
    entities = [
        BemfaLight(coordinator, mqtt_client, topic, entry)
        for topic, device in coordinator.data.items()
        if device["type"] == "light"
    ]
    
    if entities:
        async_add_entities(entities)

class BemfaLight(CoordinatorEntity, BemfaBaseEntity, LightEntity):
    """巴法云灯光设备."""

    _attr_has_entity_name = True
    _attr_color_mode = ColorMode.COLOR_TEMP
    _attr_supported_color_modes = {ColorMode.COLOR_TEMP}
    _attr_min_mireds = color_temperature_kelvin_to_mired(MAX_KELVIN)
    _attr_max_mireds = color_temperature_kelvin_to_mired(MIN_KELVIN)

    def __init__(self, coordinator, mqtt_client, topic, entry):
        """初始化巴法云灯光设备."""
        super().__init__(coordinator)
        BemfaBaseEntity.__init__(self, topic, coordinator.data[topic]["name"])
        
        self._topic = topic
        self._mqtt_client = mqtt_client
        self._api_key = entry.data[CONF_API_KEY]
        self._attr_unique_id = f"{DOMAIN}_{topic}_light"
        self._attr_name = "灯光"
        
        self._parse_state(coordinator.data[topic].get("state", ""))

    def _parse_state(self, state: str) -> None:
        """解析设备状态."""
        if not state:
            self._attr_is_on = False
            self._attr_brightness = 0
            self._attr_color_temp = self.max_mireds
            return

        parts = state.split(MSG_SEPARATOR)
        self._attr_is_on = parts[0].lower() == "on"
        
        if len(parts) > 1 and self._attr_is_on:
            try:
                brightness_pct = float(parts[1])
                self._attr_brightness = int(min(255, max(0, brightness_pct * 255 / 100)))
            except (ValueError, IndexError):
                self._attr_brightness = 255 if self._attr_is_on else 0
        else:
            self._attr_brightness = 255 if self._attr_is_on else 0

        if len(parts) > 2 and self._attr_is_on:
            try:
                kelvin = round(int(parts[2]) / 100) * 100
                kelvin = max(MIN_KELVIN, min(MAX_KELVIN, kelvin))
                self._attr_color_temp = color_temperature_kelvin_to_mired(kelvin)
            except (ValueError, IndexError):
                self._attr_color_temp = self.max_mireds
        else:
            self._attr_color_temp = self.max_mireds

    async def async_turn_on(self, **kwargs: Any) -> None:
        """打开灯."""
        brightness = kwargs.get(ATTR_BRIGHTNESS, self._attr_brightness or 255)
        color_temp = kwargs.get(ATTR_COLOR_TEMP, self._attr_color_temp)
        
        brightness_pct = max(1, min(100, round(brightness * 100 / 255)))
        kelvin = round(color_temperature_mired_to_kelvin(color_temp) / 100) * 100
        kelvin = max(MIN_KELVIN, min(MAX_KELVIN, kelvin))
        
        msg = f"on#{brightness_pct}#{kelvin}"
        await self._async_send_command(msg)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """关闭灯."""
        await self._async_send_command("off")

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