"""巴法云开关设备平台."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_API_KEY,
    MSG_ON,
    MSG_OFF,
)
from .helpers import BemfaBaseEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置巴法云开关设备."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    mqtt_client = hass.data[DOMAIN][entry.entry_id]["mqtt_client"]
    
    entities = [
        BemfaSwitch(coordinator, mqtt_client, topic, entry)
        for topic, device in coordinator.data.items()
        if device["type"] == "switch"
    ]
    
    if entities:
        async_add_entities(entities)

class BemfaSwitch(CoordinatorEntity, BemfaBaseEntity, SwitchEntity):
    """巴法云开关设备."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, mqtt_client, topic, entry):
        """初始化巴法云开关设备."""
        super().__init__(coordinator)
        BemfaBaseEntity.__init__(self, topic, coordinator.data[topic]["name"])
        
        self._topic = topic
        self._mqtt_client = mqtt_client
        self._api_key = entry.data[CONF_API_KEY]
        self._attr_unique_id = f"{DOMAIN}_{topic}_switch"
        self._attr_name = "开关"
        
        self._parse_state(coordinator.data[topic].get("state", ""))

    def _parse_state(self, state: str) -> None:
        """解析设备状态."""
        self._attr_is_on = state.lower() == MSG_ON

    async def async_turn_on(self, **kwargs: Any) -> None:
        """打开开关."""
        await self._async_send_command(MSG_ON)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """关闭开关."""
        await self._async_send_command(MSG_OFF)

    async def _async_send_command(self, command: str) -> None:
        """发送命令到巴法云."""
        try:
            self._mqtt_client.publish(f"{self._topic}/set", command)
            self._attr_is_on = command.lower() == MSG_ON
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