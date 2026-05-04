.PHONY: up down restart logs ps seed test install freeze

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose up -d --force-recreate

logs:
	docker compose logs -f web

ps:
	docker compose ps

seed:
	docker compose run --rm seeder

install:
	python -m pip install -r requirements.txt

test:
	python -m pytest -q

freeze:
	docker compose config

