"""巴法云集成组件."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

import async_timeout
import requests
import paho.mqtt.client as mqtt

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_API_KEY,
    BEMFA_API_URL,
    DEFAULT_SCAN_INTERVAL,
    DEVICE_TYPES,
    PLATFORMS,
    MQTT_HOST,
    MQTT_PORT,
    MQTT_KEEPALIVE,
    TOPIC_PING,
    INTERVAL_PING_SEND,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """设置巴法云集成."""
    hass.data.setdefault(DOMAIN, {})
    
    coordinator = BemfaDataUpdateCoordinator(
        hass,
        _LOGGER,
        entry.data[CONF_API_KEY],
        name="bemfa_devices",
        update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        raise ConfigEntryNotReady from err

    def on_connect(client, userdata, flags, rc):
        """MQTT连接回调."""
        if rc == 0:
            client.subscribe(TOPIC_PING)
            for topic in coordinator.data:
                client.subscribe(topic)

    def on_message(client, userdata, msg):
        """MQTT消息回调."""
        try:
            topic = msg.topic
            payload = msg.payload.decode()
            
            if topic == TOPIC_PING:
                coordinator._ping_lost = 0
                return
            
            if topic in coordinator.data:
                coordinator.data[topic].update({
                    "state": payload,
                    "online": True
                })
                hass.loop.call_soon_threadsafe(
                    coordinator.async_set_updated_data, 
                    coordinator.data.copy()
                )
        except Exception as err:
            _LOGGER.error("处理MQTT消息错误: %s", err)

    mqtt_client = mqtt.Client(client_id=entry.data[CONF_API_KEY])
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    try:
        mqtt_client.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE)
        mqtt_client.loop_start()
        
        async def send_ping():
            while True:
                mqtt_client.publish(TOPIC_PING, "ping")
                await asyncio.sleep(INTERVAL_PING_SEND)
        
        hass.loop.create_task(send_ping())
        
    except Exception as err:
        raise ConfigEntryNotReady("MQTT连接失败") from err

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "mqtt_client": mqtt_client,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """卸载巴法云集成."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        mqtt_client = hass.data[DOMAIN][entry.entry_id]["mqtt_client"]
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

class BemfaDataUpdateCoordinator(DataUpdateCoordinator):
    """处理巴法云数据更新的类."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        api_key: str,
        name: str,
        update_interval: timedelta,
    ) -> None:
        """初始化."""
        super().__init__(
            hass,
            logger,
            name=name,
            update_interval=update_interval,
        )
        self.api_key = api_key
        self._devices = {}
        self._ping_lost = 0

    async def _async_update_data(self):
        """获取最新的设备数据."""
        try:
            async with async_timeout.timeout(10):
                return await self._fetch_devices()
        except Exception as err:
            raise UpdateFailed(f"更新失败: {err}") from err

    async def _fetch_devices(self):
        """从巴法云获取设备列表."""
        try:
            response = await self.hass.async_add_executor_job(
                self._get_devices
            )
            
            devices = {}
            for device in response.get("data", []):
                topic = device.get("topic", "")
                device_type = self._get_device_type(topic)
                
                if device_type:
                    devices[topic] = {
                        "topic": topic,
                        "name": device.get("name", topic),
                        "type": device_type,
                        "state": device.get("msg", ""),
                        "online": True,
                    }
            
            self._devices = devices
            return devices
            
        except requests.RequestException as err:
            raise UpdateFailed("无法连接到巴法云服务器") from err

    def _get_devices(self):
        """执行API请求获取设备列表."""
        response = requests.get(
            BEMFA_API_URL,
            params={"uid": self.api_key, "type": "1"},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _get_device_type(topic: str) -> str | None:
        """根据主题确定设备类型."""
        if len(topic) >= 3:
            suffix = topic[-3:]
            if suffix in DEVICE_TYPES:
                return DEVICE_TYPES[suffix]
        
        topic_lower = topic.lower()
        if "fan" in topic_lower:
            return "fan"
        elif "switch" in topic_lower:
            return "switch"
        elif "light" in topic_lower:
            return "light"
        elif "sensor" in topic_lower:
            return "sensor"
        
        return None

    def get_device(self, topic: str):
        """获取指定主题的设备信息."""
        return self._devices.get(topic)
