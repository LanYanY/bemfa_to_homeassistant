"""巴法云传感器设备平台."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    TEMP_CELSIUS,
    PERCENTAGE,
    LIGHT_LUX,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_API_KEY,
    MSG_SEPARATOR,
    MSG_ON,
)
from .helpers import BemfaBaseEntity

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    "temperature": {
        "name": "温度",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": TEMP_CELSIUS,
        "index": 1,
    },
    "humidity": {
        "name": "湿度",
        "device_class": SensorDeviceClass.HUMIDITY,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": PERCENTAGE,
        "index": 2,
    },
    "switch": {
        "name": "开关",
        "device_class": BinarySensorDeviceClass.POWER,
        "index": 3,
    },
    "illuminance": {
        "name": "光照",
        "device_class": SensorDeviceClass.ILLUMINANCE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": LIGHT_LUX,
        "index": 4,
    },
    "pm25": {
        "name": "PM2.5",
        "device_class": SensorDeviceClass.PM25,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "index": 5,
    },
    "heart_rate": {
        "name": "心率",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": "bpm",
        "index": 6,
    },
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置巴法云传感器设备."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    mqtt_client = hass.data[DOMAIN][entry.entry_id]["mqtt_client"]
    
    entities = []
    for topic, device in coordinator.data.items():
        if device["type"] == "sensor":
            state = device.get("state", "")
            parts = state.split(MSG_SEPARATOR) if state else []
            
            entities.append(
                BemfaSensor(coordinator, mqtt_client, topic, entry, "temperature", SENSOR_TYPES["temperature"])
            )
            
            if len(parts) > 2:
                entities.append(
                    BemfaSensor(coordinator, mqtt_client, topic, entry, "humidity", SENSOR_TYPES["humidity"])
                )
            
            if len(parts) > 3:
                entities.append(
                    BemfaBinarySensor(coordinator, mqtt_client, topic, entry, "switch", SENSOR_TYPES["switch"])
                )
            
            if len(parts) > 4:
                entities.append(
                    BemfaSensor(coordinator, mqtt_client, topic, entry, "illuminance", SENSOR_TYPES["illuminance"])
                )
            
            if len(parts) > 5:
                entities.append(
                    BemfaSensor(coordinator, mqtt_client, topic, entry, "pm25", SENSOR_TYPES["pm25"])
                )
            
            if len(parts) > 6:
                entities.append(
                    BemfaSensor(coordinator, mqtt_client, topic, entry, "heart_rate", SENSOR_TYPES["heart_rate"])
                )
    
    if entities:
        async_add_entities(entities)

class BemfaSensor(CoordinatorEntity, BemfaBaseEntity, SensorEntity):
    """巴法云传感器设备."""

    def __init__(
        self,
        coordinator,
        mqtt_client,
        topic,
        entry,
        sensor_type: str,
        config: dict,
    ):
        """初始化巴法云传感器设备."""
        super().__init__(coordinator)
        BemfaBaseEntity.__init__(self, topic, coordinator.data[topic]["name"])
        
        self._topic = topic
        self._mqtt_client = mqtt_client
        self._api_key = entry.data[CONF_API_KEY]
        self._sensor_type = sensor_type
        self._config = config
        
        self._attr_unique_id = f"{DOMAIN}_{topic}_{sensor_type}"
        self._attr_name = config["name"]
        self._attr_native_unit_of_measurement = config.get("unit")
        self._attr_device_class = config.get("device_class")
        self._attr_state_class = config.get("state_class")
        
        self._parse_state(coordinator.data[topic].get("state", ""))

    def _parse_state(self, state: str) -> None:
        """解析设备状态."""
        if not state:
            self._attr_native_value = None
            return

        parts = state.split(MSG_SEPARATOR)
        index = self._config["index"]
        
        if len(parts) > index:
            try:
                value = parts[index].strip()
                if value:
                    self._attr_native_value = float(value)
                else:
                    self._attr_native_value = None
            except (ValueError, IndexError):
                self._attr_native_value = None
        else:
            self._attr_native_value = None

    @property
    def available(self) -> bool:
        """返回设备是否可用."""
        return self.coordinator.data.get(self._topic, {}).get("online", True)

    def _handle_coordinator_update(self) -> None:
        """处理设备状态更新."""
        device = self.coordinator.data.get(self._topic, {})
        self._parse_state(device.get("state", ""))
        self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)

class BemfaBinarySensor(CoordinatorEntity, BemfaBaseEntity, BinarySensorEntity):
    """巴法云二进制传感器设备."""

    def __init__(
        self,
        coordinator,
        mqtt_client,
        topic,
        entry,
        sensor_type: str,
        config: dict,
    ):
        """初始化巴法云二进制传感器设备."""
        super().__init__(coordinator)
        BemfaBaseEntity.__init__(self, topic, coordinator.data[topic]["name"])
        
        self._topic = topic
        self._mqtt_client = mqtt_client
        self._api_key = entry.data[CONF_API_KEY]
        self._sensor_type = sensor_type
        self._config = config
        
        self._attr_unique_id = f"{DOMAIN}_{topic}_{sensor_type}"
        self._attr_name = config["name"]
        self._attr_device_class = config.get("device_class")
        
        self._parse_state(coordinator.data[topic].get("state", ""))

    def _parse_state(self, state: str) -> None:
        """解析设备状态."""
        if not state:
            self._attr_is_on = None
            return

        parts = state.split(MSG_SEPARATOR)
        index = self._config["index"]
        
        if len(parts) > index:
            value = parts[index].strip().lower()
            self._attr_is_on = bool(value) and value == MSG_ON
        else:
            self._attr_is_on = None

    @property
    def available(self) -> bool:
        """返回设备是否可用."""
        return self.coordinator.data.get(self._topic, {}).get("online", True)

    def _handle_coordinator_update(self) -> None:
        """处理设备状态更新."""
        device = self.coordinator.data.get(self._topic, {})
        self._parse_state(device.get("state", ""))
        self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)