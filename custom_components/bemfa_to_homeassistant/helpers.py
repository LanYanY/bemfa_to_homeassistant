"""巴法云集成的辅助函数."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, MANUFACTURER, MODEL

@dataclass
class BemfaDeviceInfo:
    """巴法云设备信息."""
    topic: str
    name: str
    type: str
    state: str = ""
    online: bool = True

def get_device_info(topic: str, name: str) -> DeviceInfo:
    """获取设备信息."""
    return DeviceInfo(
        identifiers={(DOMAIN, topic)},
        name=name,
        manufacturer=MANUFACTURER,
        model=MODEL,
        sw_version="1.0",
        via_device=(DOMAIN, topic),
    )

class BemfaBaseEntity(Entity):
    """巴法云基础实体类."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, topic: str, name: str) -> None:
        """初始化基础实体."""
        self._attr_device_info = get_device_info(topic, name)
        self._attr_unique_id = f"{DOMAIN}_{topic}"