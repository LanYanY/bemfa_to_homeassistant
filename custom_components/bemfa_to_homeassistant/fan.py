"""巴法云风扇设备平台."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.fan import (
    FanEntity,
    FanEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.percentage import (
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)

from .const import (
    DOMAIN,
    CONF_API_KEY,
    MSG_ON,
    MSG_OFF,
    MSG_SEPARATOR,
)
from .helpers import BemfaBaseEntity

_LOGGER = logging.getLogger(__name__)

# 风扇速度列表
SPEED_LIST = [1, 2, 3, 4]

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置巴法云风扇设备."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    mqtt_client = hass.data[DOMAIN][entry.entry_id]["mqtt_client"]
    
    entities = [
        BemfaFan(coordinator, mqtt_client, topic, entry)
        for topic, device in coordinator.data.items()
        if device["type"] == "fan"
    ]
    
    if entities:
        async_add_entities(entities)

class BemfaFan(CoordinatorEntity, BemfaBaseEntity, FanEntity):
    """巴法云风扇设备."""

    _attr_has_entity_name = True
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED |
        FanEntityFeature.OSCILLATE
    )
    _attr_speed_count = len(SPEED_LIST)

    def __init__(self, coordinator, mqtt_client, topic, entry):
        """初始化巴法云风扇设备."""
        super().__init__(coordinator)
        BemfaBaseEntity.__init__(self, topic, coordinator.data[topic]["name"])
        
        self._topic = topic
        self._mqtt_client = mqtt_client
        self._api_key = entry.data[CONF_API_KEY]
        self._attr_unique_id = f"{DOMAIN}_{topic}_fan"
        self._attr_name = "风扇"
        
        self._parse_state(coordinator.data[topic].get("state", ""))

    def _parse_state(self, state: str) -> None:
        """解析设备状态."""
        if not state:
            self._attr_is_on = False
            self._attr_percentage = 0
            self._attr_oscillating = False
            return

        parts = state.split(MSG_SEPARATOR)
        self._attr_is_on = parts[0].lower() == MSG_ON
        
        if len(parts) > 1 and self._attr_is_on:
            try:
                speed = int(parts[1])
                if 1 <= speed <= 4:
                    self._attr_percentage = ordered_list_item_to_percentage(SPEED_LIST, speed)
                else:
                    self._attr_percentage = 0
            except (ValueError, IndexError):
                self._attr_percentage = 0
        else:
            self._attr_percentage = 0
        
        if len(parts) > 2 and self._attr_is_on:
            self._attr_oscillating = parts[2] == "1"
        else:
            self._attr_oscillating = False

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """打开风扇."""
        if percentage is None:
            percentage = self.percentage or ordered_list_item_to_percentage(SPEED_LIST, 1)
        
        speed = percentage_to_ordered_list_item(SPEED_LIST, percentage)
        oscillating = "1" if self.oscillating else "0"
        
        msg = f"{MSG_ON}#{speed}#{oscillating}"
        await self._async_send_command(msg)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """关闭风扇."""
        await self._async_send_command(MSG_OFF)

    async def async_set_percentage(self, percentage: int) -> None:
        """设置风扇速度."""
        if percentage == 0:
            await self.async_turn_off()
        else:
            speed = percentage_to_ordered_list_item(SPEED_LIST, percentage)
            oscillating = "1" if self.oscillating else "0"
            msg = f"{MSG_ON}#{speed}#{oscillating}"
            await self._async_send_command(msg)

    async def async_oscillate(self, oscillating: bool) -> None:
        """设置摇头状态."""
        if self.is_on:
            speed = percentage_to_ordered_list_item(SPEED_LIST, self.percentage or 25)
            msg = f"{MSG_ON}#{speed}#{'1' if oscillating else '0'}"
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