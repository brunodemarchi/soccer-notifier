import logging

import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_IDS, TIMEZONE

logger = logging.getLogger(__name__)


def _send(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    for chat_id in TELEGRAM_CHAT_IDS:
        resp = requests.post(
            url,
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
        resp.raise_for_status()
    logger.info("Notificação enviada (%d destinatários): %s", len(TELEGRAM_CHAT_IDS), text[:80])


def _local_time(match: dict) -> str:
    return match["kickoff_utc"].astimezone(TIMEZONE).strftime("%H:%M")


def send_day_before(match: dict):
    _send(
        f"🗓️ <b>Jogo amanhã!</b>\n"
        f"⚽ {match['home']} x {match['away']}\n"
        f"🏆 {match['league']}\n"
        f"🕐 {_local_time(match)} (Brasília)"
    )


def send_morning(match: dict):
    _send(
        f"☀️ <b>Tem jogo hoje!</b>\n"
        f"⚽ {match['home']} x {match['away']}\n"
        f"🏆 {match['league']}\n"
        f"🕐 {_local_time(match)} (Brasília)"
    )


def send_pre_match(match: dict):
    _send(
        f"🚨 <b>Começa em 5 minutos!</b>\n"
        f"⚽ {match['home']} x {match['away']}\n"
        f"🏆 {match['league']}"
    )
