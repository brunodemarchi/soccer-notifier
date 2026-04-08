import logging

import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_IDS, TIMEZONE

logger = logging.getLogger(__name__)


def _send_to(chat_id: str | int, text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    resp = requests.post(
        url,
        json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
        timeout=10,
    )
    resp.raise_for_status()


def _send(text: str):
    for chat_id in TELEGRAM_CHAT_IDS:
        _send_to(chat_id, text)
    logger.info("Notificação enviada (%d destinatários): %s", len(TELEGRAM_CHAT_IDS), text[:80])


def _local_time(match: dict) -> str:
    return match["kickoff_utc"].astimezone(TIMEZONE).strftime("%H:%M")


def _match_block(match: dict, include_time: bool = True) -> str:
    block = f"⚽ {match['home']} x {match['away']}\n🏆 {match['league']}"
    if include_time:
        block += f"\n🕐 {_local_time(match)} (Brasília)"
    return block


def _send_batch(matches: list[dict], singular: str, plural: str, include_time: bool = True):
    heading = singular if len(matches) == 1 else plural
    body = "\n\n".join(_match_block(m, include_time) for m in matches)
    sep = "\n" if len(matches) == 1 else "\n\n"
    _send(f"{heading}{sep}{body}")


def send_day_before(matches: list[dict]):
    _send_batch(matches, "🗓️ <b>Jogo amanhã!</b>", "🗓️ <b>Jogos amanhã!</b>")


def send_morning(matches: list[dict]):
    _send_batch(matches, "☀️ <b>Tem jogo hoje!</b>", "☀️ <b>Tem jogos hoje!</b>")


def send_pre_match(matches: list[dict]):
    _send_batch(matches, "🚨 <b>Começa em 5 minutos!</b>", "🚨 <b>Começam em 5 minutos!</b>", include_time=False)
