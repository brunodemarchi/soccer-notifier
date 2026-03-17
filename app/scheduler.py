import logging
from datetime import datetime, timedelta

import pytz
from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.schedulers.background import BackgroundScheduler

from api import get_upcoming_fixtures, parse_fixture
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


def _job_id(match_id: str, ntype: str) -> str:
    return f"{match_id}__{ntype}"


def _execute_notification(func, match: dict, ntype: str):
    """Wrapper called by APScheduler. Sends message and marks as sent."""
    try:
        func(match)
        mark_sent(match["id"], ntype)
    except Exception:
        logger.exception("Erro ao enviar notificação %s para partida %s", ntype, match["id"])
        raise  # re-raise so APScheduler registers the failure


def _schedule_one(run_at: datetime, match: dict, ntype: str, func):
    now = datetime.now(tz=TIMEZONE)

    if run_at <= now:
        logger.debug("Pulando %s para %s: horário já passou (%s)", ntype, match["id"], run_at)
        return

    if is_sent(match["id"], ntype):
        return  # already sent in a previous run

    job_id = _job_id(match["id"], ntype)
    if scheduler.get_job(job_id):
        return  # already queued in memory

    scheduler.add_job(
        _execute_notification,
        trigger="date",
        run_date=run_at,
        id=job_id,
        args=[func, match, ntype],
        misfire_grace_time=_GRACE[ntype],
    )
    logger.info("Agendado [%s] para %s", job_id, run_at.strftime("%Y-%m-%d %H:%M %Z"))


def _schedule_match(match: dict):
    kickoff_local = match["kickoff_utc"].astimezone(TIMEZONE)
    d = kickoff_local.date()

    # 20:00 the day before
    day_before_at = TIMEZONE.localize(datetime(d.year, d.month, d.day, 20, 0)) - timedelta(days=1)

    # 09:00 on match day
    morning_at = TIMEZONE.localize(datetime(d.year, d.month, d.day, 9, 0))

    # 5 minutes before kickoff
    pre_match_at = kickoff_local - timedelta(minutes=5)

    _schedule_one(day_before_at, match, "day_before", send_day_before)
    _schedule_one(morning_at,    match, "morning",    send_morning)
    _schedule_one(pre_match_at,  match, "pre_match",  send_pre_match)


def fetch_and_schedule():
    logger.info("Buscando próximas partidas...")
    for team in TEAMS:
        fixtures = get_upcoming_fixtures(team["id"], next_n=10)
        logger.info("Time %s → %d partidas encontradas", team["name"], len(fixtures))
        for raw in fixtures:
            try:
                match = parse_fixture(raw)
                _schedule_match(match)
            except Exception:
                logger.exception("Erro ao processar partida: %s", raw)
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
