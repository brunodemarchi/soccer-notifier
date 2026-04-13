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


def _local_kickoff(match: dict, fmt: str) -> str:
    return match["kickoff_utc"].astimezone(TIMEZONE).strftime(fmt)


def _match_block(match: dict, time_fmt: str | None = "%H:%M") -> str:
    teams = " / ".join(match.get("teams", []))
    lines = []
    if teams:
        lines.append(f"<b>{teams}</b>")
    lines.append(f"⚽ {match['home']} x {match['away']}")
    lines.append(f"🏆 {match['league']}")
    if time_fmt:
        lines.append(f"🕐 {_local_kickoff(match, time_fmt)} (Brasília)")
    return "\n".join(lines)


def _send_batch(
    matches: list[dict],
    singular: str,
    plural: str,
    time_fmt: str | None = "%H:%M",
    sender=_send,
):
    heading = singular if len(matches) == 1 else plural
    body = "\n\n".join(_match_block(m, time_fmt) for m in matches)
    sep = "\n" if len(matches) == 1 else "\n\n"
    sender(f"{heading}{sep}{body}")


def send_day_before(matches: list[dict]):
    _send_batch(matches, "🗓️ <b>Jogo amanhã!</b>", "🗓️ <b>Jogos amanhã!</b>")


def send_morning(matches: list[dict]):
    _send_batch(matches, "☀️ <b>Tem jogo hoje!</b>", "☀️ <b>Tem jogos hoje!</b>")


def send_pre_match(matches: list[dict]):
    _send_batch(matches, "🚨 <b>Começa em 5 minutos!</b>", "🚨 <b>Começam em 5 minutos!</b>", time_fmt=None)


def send_proximos(matches: list[dict], sender=_send):
    _send_batch(
        matches,
        "📅 <b>Próximo jogo</b>",
        "📅 <b>Próximos jogos</b>",
        time_fmt="%d/%m/%Y %H:%M",
        sender=sender,
    )
