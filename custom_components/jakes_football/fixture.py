"""Data types to make handling of fixtures easier."""

from typing import Any


class FixtureData:
    """Stores all data for a single fixture."""

    def __init__(self, data: Any = None) -> None:
        """Initialise from json data."""
        if data is None:
            self.is_valid = False
            return

        self.fixture = Fixture(data["fixture"])
        self.competition = League(data["league"])
        self.home_team = Team(data["teams"]["home"])
        self.away_team = Team(data["teams"]["away"])

        self.goals: Goals | None = None
        self.penalty_shootout: Goals | None = None
        if self.fixture.status.elapsed > 0:
            self.goals = Goals(data["goals"])
            self.penalty_shootout = Goals(data["score"]["penalty"])

        self.is_valid = True

    def get_attributes(self) -> dict[str, Any]:
        """Convert this to a dict to use as attributes."""
        out: dict[str, Any] = {}
        if self.is_valid is False:
            return out

        out["fixture"] = self.fixture.get_attributes()
        out["competition"] = self.competition.get_attributes()
        out["home_team"] = self.home_team.get_attributes()
        out["away_team"] = self.away_team.get_attributes()

        if self.goals is not None:
            out["goals"] = self.goals.get_attributes()
        else:
            out["goals"] = None

        if self.penalty_shootout is not None:
            out["penalty_shootout"] = self.penalty_shootout.get_attributes()
        else:
            out["goals"] = None
        return out


class Fixture:
    """Stores all data relating to the fixture event."""

    def __init__(self, data) -> None:
        """Initialise from json data."""
        self.id = data["id"]
        self.timestamp = data["timestamp"]
        self.date = data["date"]
        self.timezone = data["timezone"]
        self.kick_off_time = data["periods"]["first"]
        self.second_half_time = data["periods"]["second"]
        self.stadium = data["venue"]["name"]
        self.location = data["venue"]["city"]
        self.status = Status(data["status"])

    def get_attributes(self) -> dict[str, Any]:
        """Convert this to a dict to make accessible via attributes."""
        out: dict[str, Any] = {}
        out["id"] = self.id
        out["date"] = self.date
        out["timezone"] = self.timezone
        out["kick_off_time"] = self.kick_off_time
        out["second_half_time"] = self.second_half_time
        out["stadium"] = self.stadium
        out["location"] = self.location
        out["status"] = self.status.get_attributes()
        return out

    def is_in_play(self) -> bool:
        """Return true if this match has kicked off and hasn't ended yet (including suspended matches)."""
        in_play_statuses = ["1H", "HT", "2H", "ET", "BT", "P", "SUSP", "INT"]

        return self.status.short in in_play_statuses


class Status:
    """Stores data relating to the status of the match."""

    def __init__(self, data) -> None:
        """Initialise from json data."""
        self.long = data["long"]
        self.short = data["short"]
        self.elapsed = data["elapsed"]

    def get_attributes(self) -> dict[str, Any]:
        """Convert this to a dict to make accessible via attributes."""
        out: dict[str, Any] = {}
        out["long"] = self.long
        out["short"] = self.short
        out["elapsed"] = self.elapsed
        return out


class League:
    """Stores all data for the competition this fixture is in."""

    def __init__(self, data) -> None:
        """Initialise from json data."""
        self.id = data["id"]
        self.name = data["name"]
        self.round = data["round"]

    def get_attributes(self) -> dict[str, Any]:
        """Convert this to a dict to make accessible via attributes."""
        out: dict[str, Any] = {}
        out["id"] = self.id
        out["name"] = self.name
        out["round"] = self.round
        return out


class Team:
    """Stores all data for one team."""

    def __init__(self, data) -> None:
        """Initialise from json data."""
        self.name = data["name"]
        self.logo = data["logo"]
        self.winner = data["winner"]

    def get_attributes(self) -> dict[str, Any]:
        """Convert this to a dict to make accessible via attributes."""
        out: dict[str, Any] = {}
        out["name"] = self.name
        out["logo"] = self.logo
        out["winner"] = self.winner
        return out


class Goals:
    """Stores data for goals. Can be for the whole match, a half, or in penalties."""

    def __init__(self, data) -> None:
        """Initialise from json data."""
        self.home = data["home"]
        self.away = data["away"]

    def get_attributes(self) -> dict[str, Any]:
        """Convert this to a dict to make accessible via attributes."""
        out: dict[str, Any] = {}
        out["home"] = self.home
        out["away"] = self.away
        return out
