"""Database migration script for production startup."""

import logging
import sys

from alembic.config import Config

from alembic import command

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_migrations() -> bool:
    """
    Run database migrations.

    Returns:
        bool: True if migrations succeeded, False otherwise
    """
    try:
        logger.info("Running database migrations...")

        # Load alembic config
        alembic_cfg = Config("alembic.ini")

        # Run migrations to head
        logger.debug("Calling alembic upgrade...")
        command.upgrade(alembic_cfg, "head")
        logger.debug("Alembic upgrade completed")

        logger.info("Database migrations completed successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to run migrations: {e}", exc_info=True)
        return False


def main():
    """Run migrations and exit with appropriate code."""
    success = run_migrations()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
