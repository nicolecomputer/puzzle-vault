.PHONY: dev start db-migrate db-makemigration db-seed db-reset test format lint typecheck import run-agent-worker

dev:
	DATA_PATH=./data uv run honcho start -f Procfile.dev


import:
	DATA_PATH=./data uv run python -m src.importer.main

run-agent-worker:
	DATA_PATH=./data uv run python -m src.agents.worker

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
	uv run ty check src/
