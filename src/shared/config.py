"""Application configuration management."""

import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
# ENV_PATH can be set as an environment variable (e.g., in Docker)
# If not set, defaults to data/config/.env in the project root
env_path = os.getenv(
    "ENV_PATH", str(Path(__file__).parent.parent / "data" / "config" / ".env")
)
load_dotenv(dotenv_path=env_path, override=False)


class Settings:
    """Application settings loaded from environment variables."""

    # Session secret key for encrypting session cookies
    # If not set in environment, generate a random one (will change on restart)
    SESSION_SECRET_KEY: str = os.getenv("SESSION_SECRET_KEY", secrets.token_hex(32))

    # Session timeout in seconds (default: 1 hour)
    SESSION_MAX_AGE: int = int(os.getenv("SESSION_MAX_AGE", "3600"))

    # Data path for all application data (database, config, puzzles)
    DATA_PATH: Path = Path(
        os.getenv("DATA_PATH", Path(__file__).parent.parent / "data")
    )

    def __init__(self) -> None:
        """Ensure directories exist."""
        self.DATA_PATH.mkdir(parents=True, exist_ok=True)
        self.config_path.mkdir(parents=True, exist_ok=True)
        self.puzzles_path.mkdir(parents=True, exist_ok=True)

    @property
    def config_path(self) -> Path:
        """Get the config directory path."""
        return self.DATA_PATH / "config"

    @property
    def database_url(self) -> str:
        """Get the database URL."""
        db_path = self.DATA_PATH / "puzfeed.db"
        return f"sqlite:///{db_path}"

    @property
    def puzzles_path(self) -> Path:
        """Get the puzzles directory path."""
        return self.DATA_PATH / "puzzles"


# Global settings instance
settings = Settings()

# Warn if using auto-generated session secret
if "SESSION_SECRET_KEY" not in os.environ:
    print("⚠️  WARNING: SESSION_SECRET_KEY not set in environment!")
    print("   Sessions will not persist across server restarts.")
    print("   Set SESSION_SECRET_KEY in data/config/.env for persistent sessions.")
    print(
        '   You can generate one with: python -c "import secrets; print(secrets.token_hex(32))"'
    )
