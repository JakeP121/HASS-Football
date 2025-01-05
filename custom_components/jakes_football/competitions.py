"""Data type to make handling of competitions easier."""

from datetime import datetime


def get_season_number() -> int:
    """Get the year of the current season (August-July)."""
    now = datetime.now()
    if now.month >= 6:
        return now.year
    else:  # noqa: RET505
        return now.year - 1


class Competitions:
    """Stores all competition a club has (or will) take part in this season."""

    def __init__(self, data) -> None:
        """Initialise base data."""
        self.season_number = get_season_number()
        self.competitions: list[Competition] = []

        for competition_data in data:
            for season in competition_data["seasons"]:
                if season["year"] == self.season_number:
                    self.competitions.append(
                        Competition(competition_data, self.season_number)
                    )


class Competition:
    """Stores data about a competition."""

    def __init__(self, data, season_number) -> None:
        """Initialise base data."""
        self.id: int = int(data["league"]["id"])
        self.name: str = data["league"]["name"]
        self.type: str = data["league"]["type"]
        self.logo: str = data["league"]["logo"]
        self.season_number: int = int(season_number)
