# Configuration Directory

This directory contains:
- **puz-feed.db** - SQLite database file (created by migrations)
- **.env** - Environment variables and configuration (gitignored)
- **.env.example** - Template for environment configuration

## Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp config/.env.example config/.env
   ```

2. Edit `.env` with your configuration

3. Run database migrations:
   ```bash
   pipenv run migrate
   ```

The database file (`puz-feed.db`) will be automatically created when you run migrations.

## Migrations

This project uses Alembic for database migrations:

- **Run migrations**: `pipenv run migrate`
- **Create new migration**: `pipenv run makemigration "description of change"`
- **Check current version**: `pipenv run alembic current`
- **View migration history**: `pipenv run alembic history`

## Docker

When running in Docker, mount this entire directory as a volume:

```yaml
volumes:
  - ./config:/app/config
```

This persists both the database and configuration outside the container.
