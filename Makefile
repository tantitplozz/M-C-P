# OMNI AGENT STACK - Makefile
# Secret Technique: Use .PHONY to ensure commands run regardless of file names.
# Use self-documenting style for clarity.

.DEFAULT_GOAL := help

# Use the shell defined here, and not the user's default shell
SHELL=/bin/bash

# Load environment variables from .env file
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

.PHONY: help
help: ## ✨ Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: up
up: ## 🚀 Build and start all services in detached mode
	@echo "Starting OMNI AGENT STACK..."
	docker compose up --build -d

.PHONY: down
down: ## 🛑 Stop and remove all services
	@echo "Stopping OMNI AGENT STACK..."
	docker compose down

.PHONY: ps
ps: ## 📊 Show status of running services
	@docker compose ps

.PHONY: logs
logs: ## 📜 Tail logs from all services
	@docker compose logs -f

.PHONY: logs-service
logs-service: ## 📜 Tail logs from a specific service (e.g., make logs-service s=api_gateway)
	@docker compose logs -f $(s)

.PHONY: prune
prune: ## 🧹 Clean up the system: remove stopped containers, dangling images, and unused volumes/networks
	@echo "Pruning Docker system..."
	docker system prune -af
	docker volume prune -f

.PHONY: shell
shell: ## 💻 Access shell of a running service (e.g., make shell s=orchestrator)
	@docker compose exec $(s) /bin/sh

.PHONY: test
test: ## 🧪 Run tests for all services that have them
	@echo "Running tests..."
	# This is a placeholder. Each service should have its own test command.
	# Example: docker compose run --rm api_gateway go test ./...
	@echo "No tests configured yet."

.PHONY: lint
lint: ## 🎨 Lint and format code for all services
	@echo "Linting and formatting..."
	# Placeholder for linting commands
	@echo "No linters configured yet."
