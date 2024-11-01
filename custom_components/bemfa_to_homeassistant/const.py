"""巴法云集成的常量定义."""
from typing import Final
from homeassistant.const import Platform
from enum import StrEnum

DOMAIN: Final = "bemfa_to_homeassistant"
CONF_API_KEY: Final = "api_key"

# MQTT 设置
MQTT_HOST: Final = "bemfa.com"
MQTT_PORT: Final = 9501
MQTT_KEEPALIVE: Final = 600

TOPIC_PREFIX: Final = "hass"
TOPIC_PING: Final = f"{TOPIC_PREFIX}ping"

# MQTT 心跳间隔
INTERVAL_PING_SEND: Final = 30
INTERVAL_PING_RECEIVE: Final = 20  
MAX_PING_LOST: Final = 3

# 消息格式
MSG_SEPARATOR: Final = "#"
MSG_ON: Final = "on"
MSG_OFF: Final = "off"

# API URLs
BEMFA_API_URL: Final = "https://apis.bemfa.com/va/alltopic"

# 更新间隔
DEFAULT_SCAN_INTERVAL: Final = 30

# 设备信息
MANUFACTURER = "巴法云"
MODEL = "巴法云智能设备"

# 支持的平台
PLATFORMS: Final = [
    Platform.LIGHT,
    Platform.SWITCH,
    Platform.FAN,
    Platform.SENSOR,
    Platform.CLIMATE,
    Platform.COVER,
]

class BemfaDeviceType(StrEnum):
    """巴法云设备类型."""
    SWITCH = "001"
    LIGHT = "002"
    FAN = "003"
    SENSOR = "004"
    CLIMATE = "005"
    SWITCH_PANEL = "006"
    COVER = "009"

# 设备类型映射
DEVICE_TYPES = {
    BemfaDeviceType.SWITCH: "switch",
    BemfaDeviceType.LIGHT: "light", 
    BemfaDeviceType.FAN: "fan",
    BemfaDeviceType.SENSOR: "sensor",
    BemfaDeviceType.CLIMATE: "climate",
    BemfaDeviceType.SWITCH_PANEL: "switch",
    BemfaDeviceType.COVER: "cover",
}
