"""Provides an interface to the api-sports API to allow us to get fixtures data."""

from collections.abc import Mapping

import requests

from .exceptions import CannotConnect, InvalidAuth


class SportsAPI:
    """Handles all calls to api-football. Home assistant integration should get all its data through this."""

    def __init__(self, api_key: str, timeout: float = 10.0) -> None:
        """Initialise the base data."""
        self.base_url = "https://v3.football.api-sports.io/"
        self.api_key = api_key
        self.timeout = timeout

    def get_headers(self) -> Mapping[str, str | bytes]:
        """Return the header needed for the api-football endpoints."""
        return {"x-apisports-key": self.api_key}

    def get(self, endpoint: str) -> requests.Response:
        """Fire a Get request to the endpoint."""
        r = requests.get(
            self.base_url + endpoint,
            headers=self.get_headers(),
            timeout=self.timeout,
        )

        self.check_response(r)
        return r

    def check_response(self, response):
        """Check the response from an endpoint for errors."""
        if response.status_code != 200:
            raise CannotConnect

        errors = response.json()["errors"]
        if len(errors) > 0:
            raise InvalidAuth

    def check_status(self):
        """Hits the status endpoint and make sure it returns no errors."""
        self.get("status")
