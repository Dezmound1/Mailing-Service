.PHONY: up down build test lint import shell logs

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

test:
	uv run pytest -v

lint:
	uv run ruff check . && uv run ruff format --check

import:
	docker compose exec app uv run python manage.py import_mailings $(FILE)

shell:
	docker compose exec app uv run python manage.py shell

logs:
	docker compose logs -f
