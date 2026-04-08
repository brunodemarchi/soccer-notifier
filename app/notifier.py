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


def send_day_before(matches: list[dict]):
    if len(matches) == 1:
        _send(f"🗓️ <b>Jogo amanhã!</b>\n{_match_block(matches[0])}")
    else:
        body = "\n\n".join(_match_block(m) for m in matches)
        _send(f"🗓️ <b>Jogos amanhã!</b>\n\n{body}")


def send_morning(matches: list[dict]):
    if len(matches) == 1:
        _send(f"☀️ <b>Tem jogo hoje!</b>\n{_match_block(matches[0])}")
    else:
        body = "\n\n".join(_match_block(m) for m in matches)
        _send(f"☀️ <b>Tem jogos hoje!</b>\n\n{body}")


def send_pre_match(matches: list[dict]):
    if len(matches) == 1:
        _send(f"🚨 <b>Começa em 5 minutos!</b>\n{_match_block(matches[0], include_time=False)}")
    else:
        body = "\n\n".join(_match_block(m, include_time=False) for m in matches)
        _send(f"🚨 <b>Começam em 5 minutos!</b>\n\n{body}")
