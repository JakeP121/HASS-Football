"""Jake's Football Tracker integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant

from .competitions import Competition
from .const import DOMAIN, LEAGUE_DATA, TEAM_DATA
from .league import LeagueAPI
from .team import TeamAPI

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Jake's Football Tracker from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}
    api_key = entry.data[CONF_API_KEY]

    team: TeamAPI = TeamAPI(api_key=api_key, team_id=int(entry.data["team_id"]))
    hass.data[DOMAIN][entry.entry_id][TEAM_DATA] = team

    league_comp: Competition = await hass.async_add_executor_job(
        team.get_league_competition
    )

    league: LeagueAPI = LeagueAPI(api_key=api_key, league_id=league_comp.id)
    hass.data[DOMAIN][entry.entry_id][LEAGUE_DATA] = league
    team.league = league

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
