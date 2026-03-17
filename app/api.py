import logging
from datetime import datetime

import requests

from config import RAPIDAPI_KEY

logger = logging.getLogger(__name__)

_BASE_URL = "https://v3.football.api-sports.io"
_HEADERS = {
    "x-apisports-key": RAPIDAPI_KEY,
}


def get_upcoming_fixtures(team_id: int, next_n: int = 10) -> list:
    try:
        resp = requests.get(
            f"{_BASE_URL}/fixtures",
            headers=_HEADERS,
            params={"team": team_id, "next": next_n},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("response", [])
    except Exception:
        logger.exception("Falha ao buscar jogos para o time %s", team_id)
        return []


def parse_fixture(raw: dict) -> dict:
    f = raw["fixture"]
    teams = raw["teams"]
    league = raw["league"]

    # API returns ISO 8601 with offset, e.g. "2024-03-15T20:00:00+00:00"
    kickoff_utc = datetime.fromisoformat(f["date"])

    return {
        "id":          str(f["id"]),
        "home":        teams["home"]["name"],
        "away":        teams["away"]["name"],
        "league":      league["name"],
        "country":     league["country"],
        "kickoff_utc": kickoff_utc,
    }
