import logging
from datetime import datetime, timedelta, timezone

import requests

logger = logging.getLogger(__name__)

_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer"
_DAYS_AHEAD = 45

_LEAGUE_NAMES = {
    "esp.1":                    "La Liga",
    "UEFA.CHAMPIONS":           "Champions League",
    "fifa.worldq.conmebol":     "Eliminatórias Copa do Mundo",
    "fifa.world":               "Copa do Mundo",
    "conmebol.america.femenina":"Copa América Feminina",
    "fifa.wwc":                 "Copa do Mundo Feminina",
    "fifa.friendly":            "Amistoso Internacional",
    "fifa.friendly.w":          "Amistoso Internacional",
    "fifa.w.olympics":          "Olimpíadas",
}


def get_upcoming_fixtures(team_search: str, leagues: list) -> list:
    today = datetime.now(timezone.utc)
    end = today + timedelta(days=_DAYS_AHEAD)
    date_range = f"{today.strftime('%Y%m%d')}-{end.strftime('%Y%m%d')}"

    seen_ids = set()
    fixtures = []

    for league in leagues:
        url = f"{_BASE_URL}/{league}/scoreboard?dates={date_range}"
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            events = resp.json().get("events", [])
            for event in events:
                if team_search in event["name"] and event["id"] not in seen_ids:
                    seen_ids.add(event["id"])
                    fixtures.append(parse_fixture(event, league))
        except Exception:
            logger.exception("Falha ao buscar jogos [%s / %s]", team_search, league)

    return sorted(fixtures, key=lambda f: f["kickoff_utc"])


def parse_fixture(event: dict, league_slug: str) -> dict:
    kickoff_utc = datetime.fromisoformat(event["date"].replace("Z", "+00:00"))

    comp = event.get("competitions", [{}])[0]
    competitors = comp.get("competitors", [])
    home = next((c["team"]["displayName"] for c in competitors if c["homeAway"] == "home"), "")
    away = next((c["team"]["displayName"] for c in competitors if c["homeAway"] == "away"), "")
    league_name = _LEAGUE_NAMES.get(league_slug, league_slug)

    return {
        "id":          str(event["id"]),
        "home":        home,
        "away":        away,
        "league":      league_name,
        "kickoff_utc": kickoff_utc,
    }
