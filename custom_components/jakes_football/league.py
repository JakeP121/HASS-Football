"""Make calls to the League API through this object."""

from datetime import datetime
from typing import Any

from .competitions import get_season_number
from .sports_api import SportsAPI


class LeagueStanding:
    """Holds data for a single team's position in the league."""

    def __init__(self, data) -> None:
        """Initialise base data."""
        team_data = data["team"]
        self.team_id: int = int(team_data["id"])
        self.team_name: str = team_data["name"]
        self.team_logo: str = team_data["logo"]

        self.rank: int = int(data["rank"])
        self.points: int = int(data["points"])
        self.form: str = data["form"]

        stat_data = data["all"]
        self.games_played: int = int(stat_data["played"])
        self.games_won: int = int(stat_data["win"])
        self.games_tied: int = int(stat_data["draw"])
        self.games_lost: int = int(stat_data["lose"])
        self.goals_for: int = int(stat_data["goals"]["for"])
        self.goals_against: int = int(stat_data["goals"]["against"])

    def get_goal_difference(self) -> int:
        """Get goal difference."""
        return self.goals_for - self.goals_against

    def get_attributes(self) -> dict[str, Any]:
        """Convert this to a dict to use as attributes."""
        out: dict[str, Any] = {}
        out["rank"] = self.rank
        out["team_id"] = self.team_id
        out["team_name"] = self.team_name
        out["team_logo"] = self.team_logo

        out["points"] = self.points
        out["form"] = self.form

        out["games_played"] = self.games_played
        out["games_won"] = self.games_won
        out["games_tied"] = self.games_tied
        out["games_lost"] = self.games_lost
        out["goals_for"] = self.goals_for
        out["goals_against"] = self.goals_against
        out["goal_difference"] = self.goals_for - self.goals_against
        return out


class LeagueAPI(SportsAPI):
    """Holds league data that can be shared by multiple teams."""

    def __init__(self, api_key: str, league_id: int, timeout: float = 10) -> None:
        """Initialise base data."""
        super().__init__(api_key, timeout)
        self.league_id: int = int(league_id)
        self.country: str = ""
        self.name: str = ""
        self.logo: str = ""
        self.table: list[LeagueStanding] = []
        self.last_refresh: datetime | None = None

    def refresh(self, force: bool = False):
        """Try to trigger a refresh of our data."""
        now: datetime = datetime.now()

        if force or (
            self.last_refresh is not None and self.last_refresh.date() == now.date()
        ):
            return  # Already refreshed today

        r = self.get(
            "standings?league="
            + str(self.league_id)
            + "&season="
            + str(get_season_number())
        )
        response_data = r.json()["response"]
        league_data = response_data[0]["league"]
        self.country = league_data["country"]
        self.name = league_data["name"]
        self.logo = league_data["logo"]

        self.table.clear()
        for s in league_data["standings"][0]:
            self.table.append(LeagueStanding(s))

        self.last_refresh = datetime.now()

    def get_name(self) -> str:
        """Get the name of the league."""
        if self.name == "":
            self.refresh()
        return self.name

    def get_unique_name(self) -> str:
        """Get a unique name for home assistant."""
        name: str = self.get_name()
        if name == "":
            return "unknown_league"

        return name.replace(" ", "_").lower()

    def get_country(self) -> str:
        """Get the country of this league."""
        if self.country == "":
            self.refresh()
        return self.country

    def get_logo(self) -> str:
        """Get the logo of this league."""
        if self.logo == "":
            self.refresh()
        return self.logo

    def get_gameweek(self) -> int:
        """Get the current gameweek."""
        self.refresh()
        gameweek: int = 0
        for team in self.table:
            gameweek = max(gameweek, team.games_played)
        return gameweek

    def get_team_standing(self, team_id: int) -> LeagueStanding | None:
        """Get the current league position of a team."""
        self.refresh()
        for team in self.table:
            if team.team_id == team_id:
                return team
        return None

    def get_team_position(self, team_id: int) -> int:
        """Get the current league position of a team."""
        team: LeagueStanding | None = self.get_team_standing(team_id)

        if team is None:
            return -1
        return team.rank

    def get_league_leader(self) -> LeagueStanding | None:
        """Get the team at the top of the league."""
        self.refresh()
        for team in self.table:
            if team.rank == 1:
                return team
        return None

    def get_attributes(self) -> dict[str, Any]:
        """Convert this to a dict to use as attributes."""
        out: dict[str, Any] = {}
        season_number: int = get_season_number()
        out["year"] = str(season_number) + "/" + str((season_number - 2000) + 1)
        out["country"] = self.country
        out["logo"] = self.logo

        out["standings"] = []
        for team in self.table:
            out["standings"].append(team.get_attributes())

        return out
