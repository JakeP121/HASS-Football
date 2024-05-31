"""Data types to make handling of venues easier."""

from typing import Any


class Venue:
    """A stadium."""

    def __init__(self, data) -> None:
        """Initialise from json data."""
        self.id: int = int(data["id"])
        self.name: str = data["name"]
        self.address: str = data["address"]
        self.city: str = data["city"]
        self.capacity: int = int(data["capacity"])
        self.surface: str = data["surface"]
        self.image: str = data["image"]

    def get_attributes(self) -> dict[str, Any]:
        """Convert this to a dict to make accessible via attributes."""
        out: dict[str, Any] = {}
        out["id"] = self.id
        out["name"] = self.name
        out["address"] = self.address
        out["city"] = self.city
        out["capacity"] = self.capacity
        out["surface"] = self.surface
        out["image"] = self.image
        return out
