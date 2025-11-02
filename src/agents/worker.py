"""Agent worker that processes agent tasks."""

import asyncio
import logging
import sys
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.agents.registry import get_agent_class
from src.shared.database import SessionLocal
from src.shared.models.agent_task import AgentTask
from src.shared.models.source import Source

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def process_task(task: AgentTask, db: Session) -> None:
    """
    Process a single agent task.

    Args:
        task: The task to process
        db: Database session
    """
    logger.info(f"Processing task {task.id} for source {task.source_id}")

    task.status = "running"
    task.started_at = datetime.utcnow()
    db.commit()

    try:
        source = db.query(Source).filter(Source.id == task.source_id).first()
        if not source:
            raise Exception(f"Source {task.source_id} not found")

        if not source.agent_type:
            raise Exception(f"Source {source.name} has no agent type configured")

        agent_class = get_agent_class(source.agent_type)
        if not agent_class:
            raise Exception(f"Agent type {source.agent_type} not found in registry")

        agent = agent_class()
        result = await agent.fetch_puzzles(source)

        if result.success:
            task.status = "completed"
            logger.info(
                f"Task {task.id} completed successfully. Found {result.puzzles_found} puzzles"
            )
        else:
            task.status = "failed"
            logger.error(f"Task {task.id} failed: {result.error_message}")

        task.completed_at = result.completed_at or datetime.utcnow()

    except Exception:
        logger.exception(f"Error processing task {task.id}")
        task.status = "failed"
        task.completed_at = datetime.utcnow()

    db.commit()


async def worker_loop() -> None:
    """Main worker loop that polls for pending tasks."""
    logger.info("🚀 Agent worker starting...")

    while True:
        db = SessionLocal()
        try:
            stmt = (
                select(AgentTask)
                .where(AgentTask.status == "pending")
                .order_by(AgentTask.queued_at)
                .limit(1)
            )
            result = db.execute(stmt)
            task = result.scalar_one_or_none()

            if task:
                await process_task(task, db)
            else:
                await asyncio.sleep(5)

        except Exception:
            logger.exception("Error in worker loop")
            await asyncio.sleep(5)
        finally:
            db.close()


def main() -> None:
    """Entry point for the worker."""
    try:
        asyncio.run(worker_loop())
    except KeyboardInterrupt:
        logger.info("Worker stopping...")
        sys.exit(0)


if __name__ == "__main__":
    main()
