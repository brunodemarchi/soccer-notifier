import os
import pytz

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
# Comma-separated list of chat IDs, e.g. "111111111,222222222"
TELEGRAM_CHAT_IDS = [cid.strip() for cid in os.environ["TELEGRAM_CHAT_IDS"].split(",")]

TIMEZONE = pytz.timezone("America/Sao_Paulo")

# ESPN unofficial API — no key required.
# search: string matched against ESPN event name to detect the team.
# leagues: ESPN league slugs to scan for upcoming fixtures.
TEAMS = [
    {
        "name":    "Barcelona",
        "search":  "Barcelona",
        "leagues": ["esp.1", "UEFA.CHAMPIONS"],
    },
    {
        "name":    "Real Madrid",
        "search":  "Real Madrid",
        "leagues": ["esp.1", "UEFA.CHAMPIONS"],
    },
    {
        "name":    "Brasil (Masc.)",
        "search":  "Brazil",
        "leagues": ["fifa.worldq.conmebol", "fifa.world", "fifa.friendly"],
    },
    {
        "name":    "Brasil (Fem.)",
        "search":  "Brazil",
        "leagues": ["conmebol.america.femenina", "fifa.wwc", "fifa.friendly.w", "fifa.w.olympics"],
    },
]

DB_PATH = os.environ.get("DB_PATH", "/data/soccer.db")
LOG_PATH = os.environ.get("LOG_PATH", "/data/logs")
