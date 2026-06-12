"""Config flow for the Panasonic Comfort Cloud platform."""
import asyncio
import logging
from typing import Any, Dict, Optional, Mapping

import voluptuous as vol
from aiohttp import ClientError
from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from aio_panasonic_comfort_cloud import ApiClient, MFARequiredError, LoginError, ResponseError
from . import DOMAIN as PANASONIC_DOMAIN
from .const import (
    CONF_FORCE_OUTSIDE_SENSOR,
    CONF_ENABLE_DAILY_ENERGY_SENSOR,
    DEFAULT_ENABLE_DAILY_ENERGY_SENSOR,
    CONF_USE_PANASONIC_PRESET_NAMES,
    DEFAULT_USE_PANASONIC_PRESET_NAMES,
    CONF_DEVICE_FETCH_INTERVAL,
    DEFAULT_DEVICE_FETCH_INTERVAL,
    CONF_ENERGY_FETCH_INTERVAL,
    DEFAULT_ENERGY_FETCH_INTERVAL,
    CONF_FORCE_ENABLE_NANOE,
    DEFAULT_FORCE_ENABLE_NANOE)

_LOGGER = logging.getLogger(__name__)

CONF_OTP_CODE = "otp_code"

USER_SCHEMA = vol.Schema({
    vol.Required(CONF_USERNAME): str,
    vol.Required(CONF_PASSWORD): str,
    vol.Optional(CONF_ENABLE_DAILY_ENERGY_SENSOR, default=DEFAULT_ENABLE_DAILY_ENERGY_SENSOR): bool,
    vol.Optional(CONF_FORCE_ENABLE_NANOE, default=False): bool,
    vol.Optional(CONF_USE_PANASONIC_PRESET_NAMES, default=DEFAULT_USE_PANASONIC_PRESET_NAMES): bool,
    vol.Optional(CONF_DEVICE_FETCH_INTERVAL, default=DEFAULT_DEVICE_FETCH_INTERVAL): int,
    vol.Optional(CONF_ENERGY_FETCH_INTERVAL, default=DEFAULT_ENERGY_FETCH_INTERVAL): int,
})


async def _validate_credentials(hass, username: str, password: str, otp_code: str | None = None) -> str | None:
    """Try to login. Returns error key string on failure, None on success. Raises MFARequiredError."""
    client = async_get_clientsession(hass)
    api = ApiClient(username, password, client)
    await api.start_session(otp_code=otp_code)
    return None


class FlowHandler(config_entries.ConfigFlow, domain=PANASONIC_DOMAIN):
    """Handle a config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL
    _entry: config_entries.ConfigEntry | None = None
    _username: str = ""
    _password: str = ""

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return PanasonicOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """User initiated config flow."""
        errors: dict[str, str] = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]
            try:
                await _validate_credentials(self.hass, username, password)
            except MFARequiredError:
                _LOGGER.debug("MFA required for %s", username)
                self._username = username
                self._password = password
                return await self.async_step_mfa()
            except (LoginError, ResponseError):
                errors["base"] = "invalid_user_password"
            except asyncio.TimeoutError:
                errors["base"] = "device_timeout"
            except ClientError:
                errors["base"] = "device_fail"
            except Exception as e:
                _LOGGER.exception("Unexpected error during login: %s", e)
                errors["base"] = "device_fail"
            else:
                return self.async_create_entry(title="", data={
                    CONF_USERNAME: username,
                    CONF_PASSWORD: password,
                    CONF_FORCE_OUTSIDE_SENSOR: False,
                    CONF_FORCE_ENABLE_NANOE: user_input.get(CONF_FORCE_ENABLE_NANOE, DEFAULT_FORCE_ENABLE_NANOE),
                    CONF_ENABLE_DAILY_ENERGY_SENSOR: user_input.get(CONF_ENABLE_DAILY_ENERGY_SENSOR, DEFAULT_ENABLE_DAILY_ENERGY_SENSOR),
                    CONF_USE_PANASONIC_PRESET_NAMES: user_input.get(CONF_USE_PANASONIC_PRESET_NAMES, DEFAULT_USE_PANASONIC_PRESET_NAMES),
                    CONF_DEVICE_FETCH_INTERVAL: user_input.get(CONF_DEVICE_FETCH_INTERVAL, DEFAULT_DEVICE_FETCH_INTERVAL),
                    CONF_ENERGY_FETCH_INTERVAL: user_input.get(CONF_ENERGY_FETCH_INTERVAL, DEFAULT_ENERGY_FETCH_INTERVAL),
                })

        return self.async_show_form(
            step_id="user",
            data_schema=USER_SCHEMA,
            errors=errors,
        )

    async def async_step_mfa(self, user_input=None):
        """Handle 2FA/MFA OTP step during initial setup."""
        errors: dict[str, str] = {}

        if user_input is not None:
            otp_code = user_input.get(CONF_OTP_CODE, "").strip()
            try:
                await _validate_credentials(self.hass, self._username, self._password, otp_code)
            except MFARequiredError:
                errors["base"] = "mfa_failed"
            except (LoginError, ResponseError):
                errors["base"] = "invalid_user_password"
            except asyncio.TimeoutError:
                errors["base"] = "device_timeout"
            except ClientError:
                errors["base"] = "device_fail"
            except Exception as e:
                _LOGGER.exception("Unexpected MFA error: %s", e)
                errors["base"] = "mfa_failed"
            else:
                return self.async_create_entry(title="", data={
                    CONF_USERNAME: self._username,
                    CONF_PASSWORD: self._password,
                    CONF_FORCE_OUTSIDE_SENSOR: False,
                    CONF_FORCE_ENABLE_NANOE: DEFAULT_FORCE_ENABLE_NANOE,
                    CONF_ENABLE_DAILY_ENERGY_SENSOR: DEFAULT_ENABLE_DAILY_ENERGY_SENSOR,
                    CONF_USE_PANASONIC_PRESET_NAMES: DEFAULT_USE_PANASONIC_PRESET_NAMES,
                    CONF_DEVICE_FETCH_INTERVAL: DEFAULT_DEVICE_FETCH_INTERVAL,
                    CONF_ENERGY_FETCH_INTERVAL: DEFAULT_ENERGY_FETCH_INTERVAL,
                })

        return self.async_show_form(
            step_id="mfa",
            data_schema=vol.Schema({vol.Required(CONF_OTP_CODE): str}),
            errors=errors,
        )

    async def async_step_import(self, user_input):
        """Import a config entry."""
        return await self.async_step_user(user_input)

    async def async_step_reconfigure(
        self, entry_data: Mapping[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Handle reauth on failure."""
        self._entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        return await self.async_step_reconfigure_confirm()

    async def async_step_reconfigure_confirm(
        self, user_input: Mapping[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle users reauth credentials."""
        assert self._entry
        errors: dict[str, str] = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]
            try:
                await _validate_credentials(self.hass, username, password)
            except MFARequiredError:
                _LOGGER.debug("MFA required during reconfigure for %s", username)
                self._username = username
                self._password = password
                return await self.async_step_reconfigure_mfa()
            except (LoginError, ResponseError):
                errors["base"] = "invalid_user_password"
            except asyncio.TimeoutError:
                errors["base"] = "device_timeout"
            except ClientError:
                errors["base"] = "device_fail"
            except Exception as e:
                _LOGGER.exception("Unexpected reconfigure error: %s", e)
                errors["base"] = "device_fail"
            else:
                return self.async_update_reload_and_abort(
                    self._entry,
                    data={**self._entry.data, CONF_USERNAME: username, CONF_PASSWORD: password},
                )

        return self.async_show_form(
            step_id="reconfigure_confirm",
            data_schema=vol.Schema({
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }),
            errors=errors,
        )

    async def async_step_reconfigure_mfa(
        self, user_input: Mapping[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle 2FA/MFA OTP step during reconfigure."""
        assert self._entry
        errors: dict[str, str] = {}

        if user_input is not None:
            otp_code = user_input.get(CONF_OTP_CODE, "").strip()
            try:
                await _validate_credentials(self.hass, self._username, self._password, otp_code)
            except MFARequiredError:
                errors["base"] = "mfa_failed"
            except (LoginError, ResponseError):
                errors["base"] = "invalid_user_password"
            except asyncio.TimeoutError:
                errors["base"] = "device_timeout"
            except ClientError:
                errors["base"] = "device_fail"
            except Exception as e:
                _LOGGER.exception("Unexpected reconfigure MFA error: %s", e)
                errors["base"] = "mfa_failed"
            else:
                return self.async_update_reload_and_abort(
                    self._entry,
                    data={**self._entry.data, CONF_USERNAME: self._username, CONF_PASSWORD: self._password},
                )

        return self.async_show_form(
            step_id="reconfigure_mfa",
            data_schema=vol.Schema({vol.Required(CONF_OTP_CODE): str}),
            errors=errors,
        )


class PanasonicOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Panasonic options."""

    def __init__(self, config_entry):
        """Initialize Panasonic options flow."""
        self.config_entry = config_entry

    async def async_step_init(
            self, user_input: Optional[Dict[str, Any]] = None
    ) -> config_entries.ConfigFlowResult:
        """Manage Panasonic options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_ENABLE_DAILY_ENERGY_SENSOR,
                        default=self.config_entry.options.get(
                            CONF_ENABLE_DAILY_ENERGY_SENSOR, DEFAULT_ENABLE_DAILY_ENERGY_SENSOR
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_FORCE_ENABLE_NANOE,
                        default=self.config_entry.options.get(
                            CONF_FORCE_ENABLE_NANOE, DEFAULT_FORCE_ENABLE_NANOE
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_USE_PANASONIC_PRESET_NAMES,
                        default=self.config_entry.options.get(
                            CONF_USE_PANASONIC_PRESET_NAMES, DEFAULT_USE_PANASONIC_PRESET_NAMES
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_DEVICE_FETCH_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_DEVICE_FETCH_INTERVAL, DEFAULT_DEVICE_FETCH_INTERVAL
                        ),
                    ): int,
                    vol.Optional(
                        CONF_ENERGY_FETCH_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_ENERGY_FETCH_INTERVAL, DEFAULT_ENERGY_FETCH_INTERVAL
                        ),
                    ): int,
                }
            ),
        )
