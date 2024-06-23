"""Provides an interface for API calls for a single team."""

from datetime import datetime
from enum import StrEnum
import logging

from .competitions import Competitions, get_season_number
from .const import REFRESH_FREQ_MINUTES_MATCH_IN_PROGRESS
from .fixture import FixtureData
from .league import LeagueAPI
from .sports_api import SportsAPI
from .venue import Venue

_LOGGER = logging.getLogger(__name__)


class TeamType(StrEnum):
    """Different types of teams."""

    CLUB = "club"
    NATIONAL = "national"


class TeamAPI(SportsAPI):
    """An interface for API calls for a single team."""

    def __init__(self, api_key: str, team_id: int, timeout: float = 10) -> None:
        """Initialise base data."""
        SportsAPI.__init__(self, api_key, timeout)

        self.team_id: int = team_id
        self.team_name: str | None = None
        self.team_type: TeamType = TeamType.CLUB
        self.code: str | None = None
        self.country: str | None = None
        self.year_founded: int | None = None
        self.logo: str | None = None
        self.venue: Venue | None = None

        self.competitions: Competitions | None = None
        self.league: LeagueAPI | None = None

        self.last_team_refresh = None
        self.last_fixture_refresh = None
        self.next_fixture: FixtureData = FixtureData()
        self.current_fixture: FixtureData = FixtureData()
        self.previous_fixture: FixtureData = FixtureData()

    def get_team_name(self) -> str | None:
        """Get the team name from the teams endpoint."""
        if self.team_name is None:
            self.refresh_team_info()
        return self.team_name

    def get_unique_team_name(self) -> str:
        """Lowercase version of get_team_name() with no spaces."""
        team_name = self.get_team_name()
        if team_name is not None:
            return team_name.replace(" ", "_").lower()
        return "unknown_team"

    def get_team_code(self) -> str | None:
        """Get the three letter code from this team."""
        if self.code is None:
            self.refresh_team_info()
        return self.code

    def get_country(self) -> str | None:
        """Get the country this team plays in."""
        if self.country is None:
            self.refresh_team_info()
        return self.country

    def get_year_founded(self) -> int | None:
        """Get the year this team was founded."""
        if self.year_founded is None:
            self.refresh_team_info()
        return self.year_founded

    def is_national_team(self) -> bool:
        """Check if this is a club or national team."""
        if (
            self.team_name is None
        ):  # Since this only needs to be grabbed once, similarly to the team name, then refresh only if the team name is None
            self.refresh_team_info()
        return self.team_type == TeamType.NATIONAL

    def get_logo(self) -> str | None:
        """Get this team's logo."""
        if self.logo is None:
            self.refresh_team_info()
        return self.logo

    def get_venue(self) -> Venue | None:
        """Get the stadium this team plays in."""
        if self.venue is None:
            self.refresh_team_info()
        return self.venue

    def refresh_team_info(self):
        """Refresh information about this team."""
        if (
            self.last_team_refresh is not None
            and self.last_team_refresh.date() == datetime.now().date()
        ):
            return  # Already refreshed today

        r = self.get("teams?id=" + str(self.team_id))
        response_data = r.json()["response"]
        team_data = response_data[0]["team"]
        self.team_name = team_data["name"]
        self.code = team_data["code"]
        self.country = team_data["country"]
        self.year_founded = int(team_data["founded"])
        self.logo = team_data["logo"]

        if team_data["national"] is True:
            self.team_type = TeamType.NATIONAL
        else:
            self.team_type = TeamType.CLUB

        venue_data = response_data[0]["venue"]
        self.venue = Venue(venue_data)

    def get_current_fixture(self) -> FixtureData:
        """Return data about the current fixture. Refresh if needs to. Check FixtureData.is_valid to make sure there is a current fixture."""
        self.refresh_fixture_data()
        return self.current_fixture

    def get_next_fixture(self) -> FixtureData:
        """Return data about the next fixture. Refresh if needs to."""
        self.refresh_fixture_data()
        return self.next_fixture

    def get_previous_fixture(self) -> FixtureData:
        """Return data about the previous fixture. Refresh if needs to."""
        self.refresh_fixture_data()
        return self.previous_fixture

    def refresh_fixture_data(self):
        """Refresh our cached fixture data."""
        if not self.should_refresh_fixtures():
            return

        match_was_in_progress = self.current_fixture.is_valid
        self.current_fixture = FixtureData()
        self.next_fixture = FixtureData()
        self.previous_fixture = FixtureData()

        r = self.get(
            "fixtures?team=" + str(self.team_id) + "&season=" + str(get_season_number())
        )
        fixtures = r.json()["response"]
        fixtures.sort(key=lambda x: x["fixture"]["timestamp"])
        _LOGGER.debug("Found %d fixtures", len(fixtures))

        now = datetime.now()
        for fixture_json in fixtures:
            fixture_data: FixtureData = FixtureData(fixture_json)
            if fixture_data.fixture.is_in_play():
                _LOGGER.debug("Found fixture in play - %s", fixture_data.to_string())
                self.current_fixture = fixture_data
            elif fixture_data.fixture.timestamp >= now.timestamp():
                if (
                    not self.next_fixture.is_valid
                    or fixture_data.fixture.timestamp
                    < self.next_fixture.fixture.timestamp
                ):
                    self.next_fixture = fixture_data
            elif (
                not self.previous_fixture.is_valid
                or fixture_data.fixture.timestamp
                > self.previous_fixture.fixture.timestamp
            ):
                self.previous_fixture = fixture_data

        self.last_fixture_refresh = now

        if (
            match_was_in_progress
            and not self.current_fixture.is_valid  # Match was in progress but has now ended
            and self.league is not None
            and self.league.league_id
            == self.previous_fixture.competition.id  # It was a league match
        ):
            _LOGGER.debug("Refreshing league data too")
            self.league.refresh(
                True
            )  # Force a refresh of the league because the standings may have changed

    def should_refresh_fixtures(self) -> bool:
        """Check if we need to hit the API again."""
        _LOGGER.debug("should_refresh_fixtures")
        if self.last_fixture_refresh is None:
            _LOGGER.debug("TRUE - No last refresh recorded")
            return True

        time_since_refresh = datetime.now() - self.last_fixture_refresh

        # Update more frequently if a match is in progress
        if self.current_fixture.is_valid and self.current_fixture.fixture.is_in_play():
            refresh_frequency: int = REFRESH_FREQ_MINUTES_MATCH_IN_PROGRESS
            if self.current_fixture.fixture.status in ["HT", "BT"]:
                refresh_frequency = 15

            should_refresh = (time_since_refresh.seconds / 60) >= refresh_frequency
            _LOGGER.debug(
                "%s - Fixture in play and time since last refresh was %d seconds",
                "TRUE" if should_refresh else "FALSE",
                time_since_refresh.seconds,
            )
            return should_refresh

        now: datetime = datetime.now()

        # Update if we haven't updated today
        if self.last_fixture_refresh.date() != now.date():
            _LOGGER.debug("TRUE - We haven't refreshed today")
            return True

        # Update if our upcoming fixture is now in the past
        if (
            self.next_fixture.is_valid
            and self.next_fixture.fixture.timestamp <= now.timestamp()
        ):
            _LOGGER.debug("TRUE - Our upcoming fixture is now behind us")
            return True

        _LOGGER.debug("FALSE")
        return False

    def get_competitions(self) -> Competitions | None:
        """Get all competitions for this season."""
        if (
            self.competitions is not None
            and self.competitions.season_number == get_season_number()
        ):
            return self.competitions

        r = self.get("leagues?team=" + str(self.team_id))
        self.competitions = Competitions(r.json()["response"])
        return self.competitions

    def get_league_competition(self):
        """Get the league competition this season.

        Returns competition.
        """
        competition_list = self.get_competitions()
        if competition_list is None:
            return None

        for comp in competition_list.competitions:
            if comp.type == "League":
                return comp
        return None

    def get_league_position(self) -> int:
        """Get the current placement in the league."""
        if self.league is None:
            return -1
        return self.league.get_team_position(self.team_id)
