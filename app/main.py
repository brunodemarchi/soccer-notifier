import logging
import os
import sys
import time
from pathlib import Path

# ── Logging setup (must happen before importing app modules) ─────────────────
LOG_PATH = os.environ.get("LOG_PATH", "/data/logs")
Path(LOG_PATH).mkdir(parents=True, exist_ok=True)

_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
_handlers = [
    logging.StreamHandler(sys.stdout),
    logging.FileHandler(f"{LOG_PATH}/soccer-notifier.log", encoding="utf-8"),
]
for _h in _handlers:
    _h.setFormatter(_formatter)

logging.basicConfig(level=logging.INFO, handlers=_handlers)
# ─────────────────────────────────────────────────────────────────────────────

logger = logging.getLogger(__name__)

from db import init_db          # noqa: E402
from scheduler import start_scheduler  # noqa: E402


def main():
    logger.info("⚽ Soccer Notifier iniciando...")
    init_db()
    start_scheduler()
    logger.info("Rodando. CTRL+C para parar.")

    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Encerrando...")


if __name__ == "__main__":
    main()
