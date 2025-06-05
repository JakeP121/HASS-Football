"""Exceptions that can be thrown by the football API."""

from homeassistant.exceptions import HomeAssistantError


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class HTTPError(HomeAssistantError):
    """Custom error defined by a HTTP response."""
