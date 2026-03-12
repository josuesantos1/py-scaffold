APP=main:app
PORT=8000

.PHONY: help install run dev lint format fix typecheck security audit test check trivy docker-build docker-run clean

help:
	@echo "Available commands:"
	@echo " install        Install dependencies"
	@echo " run            Run API"
	@echo " dev            Run API with reload"
	@echo " lint           Run Ruff lint"
	@echo " format         Format code"
	@echo " fix            Auto-fix lint issues"
	@echo " typecheck      Run Pyright"
	@echo " security       Run Bandit"
	@echo " audit          Run pip-audit"
	@echo " test           Run tests"
	@echo " check          Run all checks"
	@echo " trivy          Scan vulnerabilities"
	@echo " docker-build   Build Docker image"
	@echo " docker-run     Run Docker container"
	@echo " clean          Clean cache"

install:
	uv sync

run:
	uv run granian --interface asgi --host 0.0.0.0 --port $(PORT) $(APP)

dev:
	uv run granian --reload --interface asgi --host 0.0.0.0 --port $(PORT) $(APP)

lint:
	uv run ruff check .

format:
	uv run ruff format .

fix:
	uv run ruff check . --fix
	uv run ruff format .

typecheck:
	uv run pyright

security:
	uv run bandit -r app -ll

audit:
	uv run pip-audit --desc

test:
	uv run pytest -q --cov=app --cov-report=term-missing --cov-fail-under=80

check: lint typecheck security audit test

trivy:
	trivy fs . --scanners vuln,secret,misconfig

docker-build:
	docker build -f prod/Dockerfile -t py-scaffold .

docker-run:
	docker run --rm -p 8000:8000 py-scaffold

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	rm -rf dist build .coverage

ci: check trivy