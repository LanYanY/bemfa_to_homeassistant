"""巴法云窗帘设备平台."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.cover import (
    CoverEntity,
    CoverEntityFeature,
    ATTR_POSITION,
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

COVER_PAUSE = "pause"

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置巴法云窗帘设备."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    mqtt_client = hass.data[DOMAIN][entry.entry_id]["mqtt_client"]
    
    entities = [
        BemfaCover(coordinator, mqtt_client, topic, entry)
        for topic, device in coordinator.data.items()
        if device["type"] == "cover"
    ]
    
    if entities:
        async_add_entities(entities)

class BemfaCover(CoordinatorEntity, BemfaBaseEntity, CoverEntity):
    """巴法云窗帘设备."""

    _attr_has_entity_name = True
    _attr_supported_features = (
        CoverEntityFeature.OPEN |
        CoverEntityFeature.CLOSE |
        CoverEntityFeature.STOP |
        CoverEntityFeature.SET_POSITION
    )

    def __init__(self, coordinator, mqtt_client, topic, entry):
        """初始化巴法云窗帘设备."""
        super().__init__(coordinator)
        BemfaBaseEntity.__init__(self, topic, coordinator.data[topic]["name"])
        
        self._topic = topic
        self._mqtt_client = mqtt_client
        self._api_key = entry.data[CONF_API_KEY]
        self._attr_unique_id = f"{DOMAIN}_{topic}_cover"
        self._attr_name = "窗帘"
        
        self._parse_state(coordinator.data[topic].get("state", ""))

    def _parse_state(self, state: str) -> None:
        """解析设备状态."""
        if not state:
            self._attr_is_closed = True
            self._attr_current_cover_position = 0
            return

        parts = state.split(MSG_SEPARATOR)
        
        if parts[0] == MSG_OFF:
            self._attr_is_closed = True
            self._attr_current_cover_position = 0
        elif parts[0] == MSG_ON:
            self._attr_is_closed = False
            self._attr_current_cover_position = 100
        elif parts[0] == COVER_PAUSE:
            pass
        
        if len(parts) > 1:
            try:
                position = int(parts[1])
                self._attr_current_cover_position = position
                self._attr_is_closed = position == 0
            except (ValueError, IndexError):
                pass

    async def async_open_cover(self, **kwargs: Any) -> None:
        """打开窗帘."""
        await self._async_send_command(MSG_ON)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """关闭窗帘."""
        await self._async_send_command(MSG_OFF)

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """停止窗帘."""
        await self._async_send_command(COVER_PAUSE)

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """设置窗帘位置."""
        position = kwargs.get(ATTR_POSITION)
        if position is not None:
            msg = f"{MSG_ON}#{position}"
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