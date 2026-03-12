"""
scheduler.py — runs the monitor cycle on a recurring interval using APScheduler.

Usage:
    python scheduler.py
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.blocking import BlockingScheduler  # type: ignore
from dotenv import load_dotenv  # type: ignore

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def monitor_job() -> None:
    from agents.orchestrator import Orchestrator

    logger.info("Scheduled monitor cycle starting ...")
    orch = Orchestrator()
    count = orch.run_monitor_cycle()
    logger.info("Scheduled monitor cycle done. Replied to %d post(s).", count)


if __name__ == "__main__":
    import yaml
    from pathlib import Path

    cfg_path = Path(__file__).parent / "config" / "settings.yaml"
    with cfg_path.open() as f:
        cfg = yaml.safe_load(f)

    interval_seconds = cfg["reddit"].get("scan_interval_seconds", 3600)

    scheduler = BlockingScheduler()
    scheduler.add_job(
        monitor_job,
        trigger="interval",
        seconds=interval_seconds,
        id="monitor_cycle",
        max_instances=1,
        coalesce=True,
    )

    logger.info("Scheduler started. Monitor cycle every %ds.", interval_seconds)
    try:
        # Run once immediately on start
        monitor_job()
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")
