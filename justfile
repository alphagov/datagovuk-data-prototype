default: help

help:
	@echo "Start the app with 'just serve' then build the search index with 'just index'."
	@echo
	@just --list

serve:
	docker compose up --build

index:
	docker compose exec web uv run flask sbox index

add package:
	docker compose exec web uv add {{package}}

shell:
	docker compose exec web /bin/bash

lint:
	docker compose exec web uv run ruff check --fix .
	docker compose exec web uv run ruff format .