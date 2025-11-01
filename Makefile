.PHONY: dev start migrate makemigration seed-data test format lint typecheck

dev:
	uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

start:
	uv run uvicorn src.main:app --host 0.0.0.0 --port 8000

migrate:
	uv run alembic upgrade head

makemigration:
	@if [ -z "$(msg)" ]; then \
		echo "Error: Migration message required. Usage: make makemigration msg=\"your message\""; \
		exit 1; \
	fi
	uv run alembic revision --autogenerate -m "$(msg)"

seed-data:
	uv run python -m scripts.seed_data

test:
	uv run pytest

format:
	uv run ruff format .

lint:
	uv run ruff check .

lint-fix:
	uv run ruff check --fix .

typecheck:
	uv run pyright src/
