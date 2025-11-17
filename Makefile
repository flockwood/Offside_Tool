.PHONY: help build up down logs restart clean migrate migrate-create shell db-shell test lint format

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build Docker containers
	docker-compose build

up: ## Start all services
	docker-compose up -d
	@echo "Services started!"
	@echo "API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
	@echo "Flower: http://localhost:5555"

down: ## Stop all services
	docker-compose down

logs: ## View logs from all services
	docker-compose logs -f

restart: ## Restart all services
	docker-compose restart

clean: ## Stop and remove containers, volumes, and images
	docker-compose down -v --remove-orphans
	@echo "Cleaned up containers, volumes, and orphaned containers"

migrate: ## Run database migrations
	docker-compose exec api alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="description")
	docker-compose exec api alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## Rollback last migration
	docker-compose exec api alembic downgrade -1

shell: ## Open a shell in the API container
	docker-compose exec api /bin/sh

db-shell: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U postgres -d soccer_analytics

redis-cli: ## Open Redis CLI
	docker-compose exec redis redis-cli

test: ## Run tests
	docker-compose exec api pytest

test-cov: ## Run tests with coverage
	docker-compose exec api pytest --cov=app tests/

lint: ## Run linting
	docker-compose exec api flake8 app/

format: ## Format code with black
	docker-compose exec api black app/
	docker-compose exec api isort app/

type-check: ## Run type checking with mypy
	docker-compose exec api mypy app/

dev: ## Start services in development mode
	docker-compose up

prod: ## Start services in production mode
	ENVIRONMENT=production docker-compose up -d

status: ## Show status of all services
	docker-compose ps

celery-logs: ## View Celery worker logs
	docker-compose logs -f celery_worker

flower: ## Open Flower monitoring dashboard
	@echo "Opening Flower at http://localhost:5555"
	@xdg-open http://localhost:5555 2>/dev/null || open http://localhost:5555 2>/dev/null || echo "Please open http://localhost:5555 in your browser"

api-docs: ## Open API documentation
	@echo "Opening API docs at http://localhost:8000/docs"
	@xdg-open http://localhost:8000/docs 2>/dev/null || open http://localhost:8000/docs 2>/dev/null || echo "Please open http://localhost:8000/docs in your browser"

install-local: ## Install dependencies locally with Poetry
	poetry install

run-local: ## Run API locally (without Docker)
	poetry run uvicorn app.main:app --reload

celery-local: ## Run Celery worker locally
	poetry run celery -A app.celery_app worker --loglevel=info

beat-local: ## Run Celery beat locally
	poetry run celery -A app.celery_app beat --loglevel=info
