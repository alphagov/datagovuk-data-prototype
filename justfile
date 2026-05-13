default: help

help:
	@echo "Start the stack with 'just serve', then seed data with 'just setup'."
	@echo
	@just --list

# Build and start the full stack
serve:
	docker compose up --build

# Add a package (stack must be running)
add package:
	docker compose exec web uv add {{package}}

# Open a shell in the web container (stack must be running)
shell:
	docker compose exec web /bin/bash
