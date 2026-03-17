import os
import pytz

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
# Comma-separated list of chat IDs, e.g. "111111111,222222222"
TELEGRAM_CHAT_IDS = [cid.strip() for cid in os.environ["TELEGRAM_CHAT_IDS"].split(",")]
RAPIDAPI_KEY = os.environ["RAPIDAPI_KEY"]

TIMEZONE = pytz.timezone("America/Sao_Paulo")

# Team IDs from API-Football (api-football-v1.p.rapidapi.com)
# To verify or find other teams: GET /teams?name=TeamName
TEAMS = [
    {"id": 529,  "name": "Barcelona",      "gender": "male"},
    {"id": 541,  "name": "Real Madrid",    "gender": "male"},
    {"id": 6,    "name": "Brasil (Masc.)", "gender": "male"},
    {"id": 1556, "name": "Brasil (Fem.)",  "gender": "female"},
]

DB_PATH = os.environ.get("DB_PATH", "/data/soccer.db")
LOG_PATH = os.environ.get("LOG_PATH", "/data/logs")
