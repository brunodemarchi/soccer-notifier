"""
Test script — run inside the container to verify API + Telegram are working.
Fetches the real next game for each team and sends a notification immediately.

Usage:
    docker exec soccer-notifier-soccer-notifier-1 python test_notify.py
"""

import logging
import os
import sys

LOG_PATH = os.environ.get("LOG_PATH", "/data/logs")
logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                    format="%(asctime)s [%(levelname)s] %(message)s")

from config import TEAMS, TIMEZONE
from api import get_upcoming_fixtures
from notifier import _send


def test():
    found_any = False

    for team in TEAMS:
        fixtures = get_upcoming_fixtures(team)
        if not fixtures:
            print(f"[{team['name']}] ⚠️  Nenhum jogo encontrado")
            continue

        match = fixtures[0]
        kickoff_local = match["kickoff_utc"].astimezone(TIMEZONE)

        message = (
            f"🧪 <b>[TESTE] Próximo jogo de {team['name']}</b>\n"
            f"⚽ {match['home']} x {match['away']}\n"
            f"🏆 {match['league']}\n"
            f"🕐 {kickoff_local.strftime('%d/%m/%Y %H:%M')} (Brasília)"
        )

        print(f"[{team['name']}] Enviando notificação de teste...")
        _send(message)
        print(f"[{team['name']}] ✅ Enviado!")
        found_any = True

    if not found_any:
        print("\n❌ Nenhuma notificação enviada. Verifique a API key e a subscrição.")
    else:
        print("\n✅ Teste concluído! Verifique o Telegram.")


if __name__ == "__main__":
    test()
