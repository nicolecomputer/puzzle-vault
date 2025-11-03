"""Agent scheduler for automatic task queueing."""

import logging
import threading
import time
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.shared.database import SessionLocal
from src.shared.models.agent_task import AgentTask
from src.shared.models.source import Source

logger = logging.getLogger(__name__)


class AgentScheduler:
    """Periodically checks schedules and queues agent tasks."""

    def __init__(self, check_interval: int = 60):
        """Initialize the scheduler.

        Args:
            check_interval: How often to check schedules in seconds (default: 60)
        """
        self.check_interval = check_interval
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self):
        """Start the scheduler."""
        self._running = True
        self._thread = threading.Thread(target=self._schedule_loop, daemon=True)
        self._thread.start()
        logger.info(
            f"Agent scheduler started (check interval: {self.check_interval} seconds)"
        )

    def stop(self):
        """Stop the scheduler."""
        logger.info("Stopping scheduler...")
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("Scheduler stopped")

    def _schedule_loop(self):
        """Main scheduling loop."""
        while self._running:
            try:
                # Sleep in 1-second intervals to respond quickly to shutdown
                for _ in range(self.check_interval):
                    if not self._running:
                        return
                    time.sleep(1)

                if not self._running:
                    break

                self._check_schedules()

            except Exception:
                logger.exception("Error in scheduler loop")

    def _check_schedules(self):
        """Check all scheduled sources and queue tasks if needed."""
        db = SessionLocal()
        try:
            stmt = select(Source).where(
                Source.schedule_enabled == True,  # noqa: E712
                Source.agent_enabled == True,  # noqa: E712
                Source.schedule_interval_hours.is_not(None),
            )
            sources = db.execute(stmt).scalars().all()

            now = datetime.now(UTC)
            for source in sources:
                try:
                    self._maybe_queue_task(source, now, db)
                except Exception:
                    logger.exception(f"Error checking schedule for source {source.id}")

            db.commit()

        except Exception:
            logger.exception("Error checking schedules")
            db.rollback()
        finally:
            db.close()

    def _maybe_queue_task(self, source: Source, now: datetime, db: Session) -> None:
        """Queue a task for a source if it's time to run.

        Args:
            source: The source to check
            now: Current time
            db: Database session
        """
        # If never run before, initialize and queue immediately
        if source.last_scheduled_run_at is None:
            logger.info(f"First scheduled run for source {source.name}, queueing task")
            self._queue_task(source, now, db)
            return

        # Calculate next run time
        next_run = source.next_run_at
        if next_run is None:
            return

        # Check if it's time to run
        if now < next_run:
            return

        # 1-minute cooldown: don't run if last run was less than a minute ago
        cooldown_period = timedelta(minutes=1)
        last_run = source.last_scheduled_run_at
        # Ensure last_run is timezone-aware for comparison (backward compatibility)
        if last_run and last_run.tzinfo is None:
            last_run = last_run.replace(tzinfo=UTC)
        if last_run and now - last_run < cooldown_period:
            logger.debug(
                f"Cooldown active for source {source.name}, skipping scheduled run"
            )
            return

        # Check if there's already a pending or running task
        stmt = select(AgentTask).where(
            AgentTask.source_id == source.id,
            AgentTask.status.in_(["pending", "running"]),
        )
        existing_task = db.execute(stmt).scalar_one_or_none()

        if existing_task:
            logger.debug(
                f"Task already exists for source {source.name} (status: {existing_task.status}), skipping"
            )
            return

        # Queue the task
        logger.info(
            f"Scheduled run due for source {source.name} (interval: {source.schedule_interval_hours}h), queueing task"
        )
        self._queue_task(source, now, db)

    def _queue_task(self, source: Source, now: datetime, db: Session) -> None:
        """Create a task and update last_scheduled_run_at.

        Args:
            source: The source to queue a task for
            now: Current time
            db: Database session
        """
        task = AgentTask(source_id=source.id, status="pending")
        db.add(task)

        source.last_scheduled_run_at = now

        logger.info(
            f"Queued task {task.id} for source {source.name}, next run at {source.next_run_at}"
        )
