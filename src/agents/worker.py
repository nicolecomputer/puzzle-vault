"""Agent worker that processes agent tasks."""

import asyncio
import logging
import sys
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.agents.agent_logger import AgentLogger, AgentLogHandler
from src.agents.registry import get_agent_class
from src.agents.scheduler import AgentScheduler
from src.shared.config import settings
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
    task.started_at = datetime.now(UTC)
    db.commit()

    # Get source
    source = db.query(Source).filter(Source.id == task.source_id).first()
    if not source:
        logger.error(f"Source {task.source_id} not found")
        task.status = "failed"
        task.completed_at = datetime.now(UTC)
        db.commit()
        return

    # Initialize agent logger
    agent_logger = AgentLogger(source, settings.DATA_PATH)
    agent_logger.info("Agent task started", task_id=str(task.id))

    # Add handler to capture root logger output
    log_handler = AgentLogHandler(agent_logger)
    log_handler.setLevel(logging.INFO)
    root_logger = logging.getLogger()
    root_logger.addHandler(log_handler)

    try:
        if not source.agent_type:
            error_msg = f"Source {source.name} has no agent type configured"
            agent_logger.error(error_msg)
            raise Exception(error_msg)

        agent_class = get_agent_class(source.agent_type)
        if not agent_class:
            error_msg = f"Agent type {source.agent_type} not found in registry"
            agent_logger.error(error_msg)
            raise Exception(error_msg)

        agent_logger.info(f"Running agent: {source.agent_type}")
        agent = agent_class()
        result = await agent.fetch_puzzles(source)

        if result.success:
            task.status = "completed"
            agent_logger.info(
                "Agent completed successfully",
                puzzles_found=result.puzzles_found,
            )
            logger.info(
                f"Task {task.id} completed successfully. Found {result.puzzles_found} puzzles"
            )
        else:
            task.status = "failed"
            agent_logger.error(
                "Agent failed",
                error_message=result.error_message,
            )
            logger.error(f"Task {task.id} failed: {result.error_message}")

        task.completed_at = result.completed_at or datetime.now(UTC)

        # Save log file
        log_file = agent_logger.save(
            success=result.success,
            puzzles_found=result.puzzles_found,
            error_message=result.error_message,
        )
        logger.info(f"Agent log saved to {log_file}")

    except Exception as e:
        logger.exception(f"Error processing task {task.id}")
        agent_logger.exception("Unexpected error during agent execution", e)
        task.status = "failed"
        task.completed_at = datetime.now(UTC)

        # Save log file with error
        log_file = agent_logger.save(
            success=False,
            error_message=str(e),
        )
        logger.info(f"Agent error log saved to {log_file}")

    finally:
        # Remove handler
        root_logger.removeHandler(log_handler)

    db.commit()


async def worker_loop() -> None:
    """Main worker loop that polls for pending tasks."""
    logger.info("🚀 Agent worker starting...")

    # Ensure agents folder exists
    agents_path = settings.DATA_PATH / "agents"
    agents_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"✓ Ensured agents folder exists: {agents_path}")

    # Ensure folder structure exists for all agent-enabled sources
    db = SessionLocal()
    try:
        sources = db.query(Source).filter(Source.agent_enabled).all()
        for source in sources:
            source.create_folders(settings.puzzles_path)
            logger.info(f"✓ Ensured folder structure for source: {source.name}")
    except Exception as e:
        logger.exception(f"Error creating source folders: {e}")
    finally:
        db.close()

    # Start the scheduler
    scheduler = AgentScheduler(check_interval=60)
    scheduler.start()

    try:
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
    finally:
        scheduler.stop()


def main() -> None:
    """Entry point for the worker."""
    try:
        asyncio.run(worker_loop())
    except KeyboardInterrupt:
        logger.info("Worker stopping...")
        sys.exit(0)


if __name__ == "__main__":
    main()
