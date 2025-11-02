"""Application configuration management."""

import configparser
import os
import secrets
from pathlib import Path


def _load_or_create_config(
    config_file: Path, template_file: Path
) -> configparser.ConfigParser:
    """
    Load configuration from INI file, creating it from template if needed.

    Returns a ConfigParser instance with the loaded configuration.
    """
    config = configparser.ConfigParser()

    # Ensure the directory exists
    config_file.parent.mkdir(parents=True, exist_ok=True)

    # If config file doesn't exist, create it from template
    if not config_file.exists():
        if not template_file.exists():
            raise FileNotFoundError(
                f"Config template not found at {template_file}. "
                "This file should be checked into version control."
            )

        # Read template and replace placeholders
        with open(template_file) as f:
            template_content = f.read()

        # Generate a new secret key
        secret_key = secrets.token_hex(32)
        config_content = template_content.format(secret_key=secret_key)

        # Write the config file
        with open(config_file, "w") as f:
            f.write(config_content)

        print(f"✓ Created new config file at {config_file}")
        print("✓ Generated session secret key")

    # Load the config file
    config.read(config_file)

    return config


# Determine data path - ONLY environment variable the app accepts
DATA_PATH = Path(os.getenv("DATA_PATH", Path(__file__).parent.parent / "data"))

# Ensure data path exists
DATA_PATH.mkdir(parents=True, exist_ok=True)

# Config file location within data path
config_file_path = DATA_PATH / "config" / "settings.ini"

# Template file location (checked into version control)
template_file_path = Path(__file__).parent.parent.parent / "config.ini.template"

# Load or create the config
_config = _load_or_create_config(config_file_path, template_file_path)


class Settings:
    """Application settings loaded from INI config file."""

    # Session secret key for encrypting session cookies
    SESSION_SECRET_KEY: str = _config.get("session", "secret_key")

    # Session timeout in seconds (default: 1 hour)
    SESSION_MAX_AGE: int = _config.getint("session", "max_age", fallback=3600)

    # Importer scan interval in seconds (default: 15 seconds)
    IMPORTER_SCAN_INTERVAL: int = _config.getint(
        "importer", "scan_interval", fallback=15
    )

    # Data path for all application data (database, config, puzzles)
    # This is set from the DATA_PATH environment variable only
    DATA_PATH: Path = DATA_PATH

    def __init__(self) -> None:
        """Ensure directories exist."""
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
