import logging
from collections import defaultdict
from datetime import datetime, timedelta

import pytz
from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.schedulers.background import BackgroundScheduler

from api import get_upcoming_fixtures
from config import TEAMS, TIMEZONE
from db import is_sent, mark_sent
from notifier import send_day_before, send_morning, send_pre_match

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone=TIMEZONE)

# Grace times: how long after the scheduled time APScheduler will still fire the job
# if the container was briefly down.
_GRACE = {
    "day_before": 3600,  # 1 hour — still useful to know the game is tomorrow
    "morning":    3600,  # 1 hour — still useful in the morning
    "pre_match":  180,   # 3 min  — after that the game has already started
}

_NOTIFY_FUNCS = {
    "day_before": send_day_before,
    "morning":    send_morning,
    "pre_match":  send_pre_match,
}


def _execute_batch(ntype: str, matches: list[dict]):
    """Send a grouped notification and mark all matches as sent."""
    try:
        _NOTIFY_FUNCS[ntype](matches)
        for match in matches:
            mark_sent(match["id"], ntype)
    except Exception:
        logger.exception("Erro ao enviar notificação %s (%d jogos)", ntype, len(matches))
        raise


def _notification_entries(match: dict) -> list[tuple]:
    """Return (run_at, ntype, match) triples, skipping past or already-sent ones."""
    now = datetime.now(tz=TIMEZONE)
    kickoff_local = match["kickoff_utc"].astimezone(TIMEZONE)
    d = kickoff_local.date()

    day_before_at = TIMEZONE.localize(datetime(d.year, d.month, d.day, 20, 0)) - timedelta(days=1)
    morning_at = TIMEZONE.localize(datetime(d.year, d.month, d.day, 9, 0))
    pre_match_at = kickoff_local - timedelta(minutes=5)

    entries = []
    for run_at, ntype in [
        (day_before_at, "day_before"),
        (morning_at, "morning"),
        (pre_match_at, "pre_match"),
    ]:
        if run_at > now and not is_sent(match["id"], ntype):
            entries.append((run_at, ntype, match))
    return entries


def fetch_and_schedule():
    logger.info("Buscando próximas partidas...")

    # Cancel all pending notification jobs — they are rebuilt from fresh ESPN
    # data every cycle so that changed dates, times, or teams are picked up.
    for job in scheduler.get_jobs():
        if job.id != "fetch_matches":
            scheduler.remove_job(job.id)

    all_entries: list[tuple] = []
    for team in TEAMS:
        fixtures = get_upcoming_fixtures(team["search"], team["leagues"])
        logger.info("Time %s → %d partidas encontradas", team["name"], len(fixtures))
        for match in fixtures:
            try:
                all_entries.extend(_notification_entries(match))
            except Exception:
                logger.exception("Erro ao processar partida: %s", match)

    # Group notifications that fire at the same moment into a single message.
    groups: dict[tuple, list[dict]] = defaultdict(list)
    seen: set[tuple[str, str]] = set()
    for run_at, ntype, match in all_entries:
        key = (match["id"], ntype)
        if key not in seen:  # deduplicate (match can appear for multiple teams)
            seen.add(key)
            groups[(run_at, ntype)].append(match)

    for (run_at, ntype), matches in groups.items():
        job_id = f"{ntype}__{run_at.strftime('%Y%m%d_%H%M')}"
        scheduler.add_job(
            _execute_batch,
            trigger="date",
            run_date=run_at,
            id=job_id,
            args=[ntype, matches],
            misfire_grace_time=_GRACE[ntype],
        )
        labels = ", ".join(f"{m['home']}×{m['away']}" for m in matches)
        logger.info("Agendado [%s] (%d jogo(s): %s) para %s",
                     job_id, len(matches), labels,
                     run_at.strftime("%Y-%m-%d %H:%M %Z"))

    logger.info("Busca concluída")


def _on_job_error(event):
    logger.error("Job falhou [%s]: %s", event.job_id, event.exception)


def start_scheduler():
    scheduler.add_listener(_on_job_error, EVENT_JOB_ERROR)

    # Fetch immediately on startup, then every 6 hours
    scheduler.add_job(
        fetch_and_schedule,
        trigger="interval",
        hours=6,
        id="fetch_matches",
        next_run_time=datetime.now(tz=pytz.utc),
    )

    scheduler.start()
    logger.info("Scheduler iniciado")
