default: help

help:
	@echo "Start the stack with 'just serve', then seed data with 'just setup'."
	@echo
	@just --list

# Seed content and generate embeddings
setup:
	docker compose exec web uv run flask sandbox content
	docker compose exec web uv run flask sandbox embed

# Force re-embed all topics
embed:
	docker compose exec web uv run flask sandbox embed --force

# Build and start the full stack
serve:
	docker compose up --build

# Build and start the full stack with search (torch + sentence-transformers)
serve-search:
	docker compose -f compose.yaml -f compose.search.yaml up --build

# Create a new migration (stack must be running)
migrate message:
	docker compose exec web uv run flask db migrate -m "{{message}}"

# Apply all pending migrations
upgrade:
	docker compose exec web uv run flask db upgrade

# Roll back one migration
downgrade:
	docker compose exec web uv run flask db downgrade

# Add a package (stack must be running)
add package:
	docker compose exec web uv add {{package}}

# Open a shell in the web container (stack must be running)
shell:
	docker compose exec web /bin/bash

# Generate requirements.txt for Heroku deployment
requirements:
	docker compose exec web uv pip compile pyproject.toml -o requirements.txt
