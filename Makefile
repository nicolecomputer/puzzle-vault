.PHONY: dev start db-migrate db-makemigration db-seed db-reset test format lint typecheck import

dev:
	DATA_PATH=./data uv run uvicorn src.web.main:app --reload --host 0.0.0.0 --port 8000

start:
	DATA_PATH=/data uv run uvicorn src.web.main:app --host 0.0.0.0 --port 8000

import:
	DATA_PATH=./data uv run python -m src.importer.processor

db-migrate:
	DATA_PATH=./data uv run alembic upgrade head

db-makemigration:
	@if [ -z "$(msg)" ]; then \
		echo "Error: Migration message required. Usage: make db-makemigration msg=\"your message\""; \
		exit 1; \
	fi
	DATA_PATH=./data uv run alembic revision --autogenerate -m "$(msg)"

db-seed:
	DATA_PATH=./data uv run python -m scripts.seed_data

db-reset:
	DATA_PATH=./data uv run python -m scripts.reset_db
	DATA_PATH=./data uv run python -m scripts.seed_data

test:
	uv run pytest -v

test-watch:
	uv run pytest -v --testmon -f

format:
	uv run ruff format .

lint:
	uv run ruff check .

lint-fix:
	uv run ruff check --fix .

typecheck:
	uv run pyright src/
