"""Football team sensor."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import ENTITY_ID_FORMAT, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTRIBUTION, DOMAIN, LEAGUE_DATA, TEAM_DATA
from .league import LeagueAPI
from .team import FixtureData, TeamAPI
from .venue import Venue

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up sensor device."""

    sensors: list[SensorEntity] = []

    teamApi: TeamAPI = hass.data[DOMAIN][entry.entry_id][TEAM_DATA]
    await hass.async_add_executor_job(teamApi.get_team_name)
    _LOGGER.info("Setting up sensor for %s", str(teamApi.get_team_name()))
    team = TeamSensor(hass, teamApi)
    sensors.append(team)

    if hass.data[DOMAIN][entry.entry_id][LEAGUE_DATA] is not None:
        leagueApi: LeagueAPI = hass.data[DOMAIN][entry.entry_id][LEAGUE_DATA]
        await hass.async_add_executor_job(leagueApi.get_name)
        _LOGGER.info("Setting up sensor for %s", str(leagueApi.get_name()))
        league = LeagueSensor(hass, leagueApi)
        sensors.append(league)

    async_add_entities(sensors)


class TeamSensor(SensorEntity):
    """Sensor to report data about a team."""

    _attr_attribution = ATTRIBUTION
    _attr_icon = "mdi:soccer"

    def __init__(self, hass: HomeAssistant, team: TeamAPI) -> None:
        """Initialise sensor attributes."""
        SensorEntity.__init__(self)
        self.hass = hass
        self.team = team

        self.entity_id = ENTITY_ID_FORMAT.format(
            f"jft_team_{team.get_unique_team_name()}"
        )
        self._attr_name = team.get_team_name()
        self._attr_unique_id = self.entity_id

        self.name: str | None = None
        self.code: str | None = None
        self.country: str | None = None
        self.year_founded: int | None = None
        self.is_national_team: bool = False
        self.logo: str | None = None
        self.venue: Venue | None = None

        self.current_fixture: FixtureData = FixtureData()
        self.next_fixture: FixtureData = FixtureData()
        self.previous_fixture: FixtureData = FixtureData()

    async def async_update(self) -> None:
        """Update all of our data asynchronously, ready for when we need to show it."""

        self.is_national_team = await self.hass.async_add_executor_job(
            self.team.is_national_team
        )

        if not self.is_national_team:
            self._attr_native_value = await self.hass.async_add_executor_job(
                self.team.get_league_position
            )
        else:
            self._attr_native_value = "National Team"

        self.name = await self.hass.async_add_executor_job(self.team.get_team_name)
        self.code = await self.hass.async_add_executor_job(self.team.get_team_code)
        self.country = await self.hass.async_add_executor_job(self.team.get_country)
        self.year_founded = await self.hass.async_add_executor_job(
            self.team.get_year_founded
        )
        self.logo = await self.hass.async_add_executor_job(self.team.get_logo)
        self.venue = await self.hass.async_add_executor_job(self.team.get_venue)

        self.current_fixture = await self.hass.async_add_executor_job(
            self.team.get_current_fixture
        )
        self.next_fixture = await self.hass.async_add_executor_job(
            self.team.get_next_fixture
        )
        self.previous_fixture = await self.hass.async_add_executor_job(
            self.team.get_previous_fixture
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return state attributes."""
        attributes: dict[str, Any] = {}

        if self.code is not None:
            attributes["code"] = self.code
        if self.country is not None:
            attributes["country"] = self.country
        if self.year_founded is not None:
            attributes["year_founded"] = self.year_founded
        if self.logo is not None:
            attributes["logo"] = self.logo
        attributes["is_national_team"] = self.is_national_team

        if self.venue is not None:
            attributes["venue"] = self.venue.get_attributes()

        if self.current_fixture.is_valid:
            attributes["current_fixture"] = self.current_fixture.get_attributes()
        if self.next_fixture.is_valid:
            attributes["next_fixture"] = self.next_fixture.get_attributes()
        if self.previous_fixture.is_valid:
            attributes["previous_fixture"] = self.previous_fixture.get_attributes()

        return attributes


class LeagueSensor(SensorEntity):
    """Sensor to report data about a league."""

    _attr_attribution = ATTRIBUTION
    _attr_icon = "mdi:format-list-bulleted"

    def __init__(self, hass: HomeAssistant, league: LeagueAPI) -> None:
        """Initialise sensor attributes."""
        SensorEntity.__init__(self)
        self.hass = hass
        self.league = league

        self.entity_id = ENTITY_ID_FORMAT.format(
            f"jft_league_{league.get_unique_name()}"
        )
        self._attr_name = league.get_name()
        self._attr_unique_id = self.entity_id

        self.gameweek: int = 0
        self.country: str = ""
        self.logo: str = ""

    async def async_update(self) -> None:
        """Update all of our data asynchronously, ready for when we need to show it."""
        self.gameweek = await self.hass.async_add_executor_job(self.league.get_gameweek)
        self._attr_native_value = self.gameweek

        self.country = await self.hass.async_add_executor_job(self.league.get_country)

        self.logo = await self.hass.async_add_executor_job(self.league.get_logo)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return state attributes."""
        attributes: dict[str, Any] = {}

        if self.league is not None:
            attributes = self.league.get_attributes()

        return attributes
