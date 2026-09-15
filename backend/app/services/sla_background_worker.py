import asyncio
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.services.sla_service import SLAService

logger = logging.getLogger("oil_safety.sla_worker")


class SLABackgroundWorker:
    """
    Non-blocking background scheduler for periodic SLA monitoring and automated escalation.
    Continuously audits active safety actions, evaluates deadlines, and triggers idempotent escalations.
    Recovers state automatically on server restarts via persistent database timestamps.
    """

    def __init__(self, check_interval_seconds: int = 30):
        self.check_interval_seconds = check_interval_seconds
        self.is_running = False
        self._task: Optional[asyncio.Task] = None

    def run_cycle(self, db: Optional[Session] = None, now: Optional[datetime] = None) -> dict:
        """
        Executes a single synchronous evaluation cycle.
        Can be invoked directly by tests, API endpoints, or periodic background loop.
        """
        close_session = False
        if db is None:
            db = SessionLocal()
            close_session = True

        try:
            res = SLAService.evaluate_and_escalate_actions(db, now=now)
            logger.info(f"[SLA Worker] Cycle executed: {res}")
            return res
        except Exception as e:
            logger.error(f"[SLA Worker] Error during evaluation cycle: {e}")
            return {"error": str(e), "evaluated_count": 0, "escalated_count": 0}
        finally:
            if close_session:
                db.close()

    async def _worker_loop(self):
        """Asynchronous periodic execution loop."""
        logger.info(f"[SLA Worker] Started with interval {self.check_interval_seconds}s")
        while self.is_running:
            try:
                await asyncio.to_thread(self.run_cycle)
            except Exception as e:
                logger.error(f"[SLA Worker] Loop exception: {e}")
            await asyncio.sleep(self.check_interval_seconds)

    def start(self):
        """Starts background worker if not already running."""
        if not self.is_running:
            self.is_running = True
            try:
                loop = asyncio.get_running_loop()
                self._task = loop.create_task(self._worker_loop())
            except RuntimeError:
                # No active event loop (e.g., during synchronous setup)
                pass

    def stop(self):
        """Stops background worker."""
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()


# Singleton instance
sla_worker = SLABackgroundWorker(check_interval_seconds=30)
