"""
Telegram bot — listens for incoming messages and responds to commands.

Commands (case-insensitive):
  proximo / proximos  — send the next upcoming game for each team
"""

import logging
import threading
import time

import requests

from api import get_upcoming_fixtures
from config import TEAMS, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_IDS, TIMEZONE
from notifier import _send_to

logger = logging.getLogger(__name__)

_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
_COMMANDS = {"proximo", "proximos"}


def _get_updates(offset: int) -> list:
    try:
        resp = requests.get(
            f"{_BASE}/getUpdates",
            params={"timeout": 30, "offset": offset},
            timeout=40,
        )
        resp.raise_for_status()
        return resp.json().get("result", [])
    except Exception:
        logger.exception("Erro ao buscar updates do Telegram")
        return None  # signals error, distinct from empty list


def _reply(chat_id: str | int, text: str):
    try:
        _send_to(chat_id, text)
    except Exception:
        logger.exception("Erro ao responder chat %s", chat_id)


def _handle_proximos(chat_id: str | int):
    found_any = False
    for team in TEAMS:
        fixtures = get_upcoming_fixtures(team["search"], team["leagues"])
        if not fixtures:
            continue

        match = fixtures[0]
        kickoff_local = match["kickoff_utc"].astimezone(TIMEZONE)
        _reply(
            chat_id,
            f"📅 <b>Próximo jogo — {team['name']}</b>\n"
            f"⚽ {match['home']} x {match['away']}\n"
            f"🏆 {match['league']}\n"
            f"🕐 {kickoff_local.strftime('%d/%m/%Y %H:%M')} (Brasília)",
        )
        found_any = True

    if not found_any:
        _reply(chat_id, "❌ Nenhum jogo encontrado para nenhum time.")


def _is_authorized(chat_id: str | int) -> bool:
    return str(chat_id) in TELEGRAM_CHAT_IDS


def _poll():
    offset = 0
    backoff = 1
    logger.info("Bot polling iniciado")
    while True:
        updates = _get_updates(offset)

        if updates is None:  # error — back off before retrying
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)
            continue

        backoff = 1
        for update in updates:
            offset = update["update_id"] + 1
            msg = update.get("message") or update.get("edited_message")
            if not msg:
                continue

            chat_id = msg["chat"]["id"]
            if not _is_authorized(chat_id):
                logger.warning("Mensagem ignorada de chat não autorizado: %s", chat_id)
                continue

            text = (msg.get("text") or "").strip().lower()
            if text in _COMMANDS:
                logger.info("Comando '%s' recebido de %s", text, chat_id)
                _handle_proximos(chat_id)


def start_bot():
    t = threading.Thread(target=_poll, name="telegram-bot", daemon=True)
    t.start()
