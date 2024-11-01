"""巴法云集成的配置流程."""
from __future__ import annotations

import logging
from typing import Any

import requests
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, CONF_API_KEY, BEMFA_API_URL

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_API_KEY): str,
})

async def validate_api_key(hass: HomeAssistant, api_key: str) -> bool:
    """验证API密钥."""
    try:
        def _validate():
            response = requests.get(
                BEMFA_API_URL,
                params={"uid": api_key, "type": "1"},
                timeout=10
            )
            response.raise_for_status()
            return response.json().get("code") == 0

        return await hass.async_add_executor_job(_validate)
    except requests.RequestException:
        return False

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """处理配置流程."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """处理用户输入."""
        errors = {}

        if user_input is not None:
            try:
                if await validate_api_key(self.hass, user_input[CONF_API_KEY]):
                    return self.async_create_entry(
                        title="巴法云",
                        data=user_input,
                    )
                errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

class CannotConnect(HomeAssistantError):
    """表示无法连接的错误."""

class InvalidAuth(HomeAssistantError):
    """表示认证无效的错误."""
