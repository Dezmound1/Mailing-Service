.PHONY: run stop build test lint import shell redis-clean

run:
	docker compose up -d

stop:
	docker compose down

build:
	docker compose build

test:
	uv run pytest -v

lint:
	uv run ruff check . && uv run ruff format --check

import:
	docker compose exec -w /app/mailing_service app uv run python manage.py import_mailings $(or $(FILE),/data/sample.xlsx) $(if $(BATCH_SIZE),--batch-size $(BATCH_SIZE)) $(if $(DRY_RUN),--dry-run)

shell:
	docker compose exec -w /app/mailing_service app uv run python manage.py shell

redis-clean:
	docker compose exec redis redis-cli FLUSHALL