# SynapseAI — Developer shortcuts
# Usage: make <target>

.PHONY: dev up down logs migrate migrate-create test lint format

## Start all services (DB + Redis + backend + worker)
up:
	docker compose up -d db redis

## Start backend dev server (local, not Docker)
dev:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

## Start frontend dev server
frontend:
	cd frontend && npm run dev

## Stop all Docker services
down:
	docker compose down

## View logs
logs:
	docker compose logs -f backend worker

## Run Alembic migrations
migrate:
	cd backend && alembic upgrade head

## Create a new migration (usage: make migrate-create MSG="add users table")
migrate-create:
	cd backend && alembic revision --autogenerate -m "$(MSG)"

## Run backend tests
test:
	cd backend && pytest -v --cov=app --cov-report=term-missing

## Lint backend
lint:
	cd backend && ruff check . && mypy app

## Format backend
format:
	cd backend && black . && ruff check --fix .

## Install backend dev deps
install:
	cd backend && pip install -e ".[dev]"

## Full reset — stop containers, remove volumes
reset:
	docker compose down -v
