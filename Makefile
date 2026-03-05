PYTHON=python
APP=app.main:app
PORT=8000

.PHONY: help install run dev lint format security audit semgrep trivy test docker-build docker-run clean

help:
	@echo "Available commands:"
	@echo " install        Install dependencies"
	@echo " run            Run API with Granian"
	@echo " dev            Run API with auto reload"
	@echo " lint           Run Ruff lint"
	@echo " format         Format code"
	@echo " security       Run Bandit"
	@echo " audit          Run pip-audit"
	@echo " trivy          Scan filesystem vulnerabilities"
	@echo " docker-build   Build Docker image"
	@echo " docker-run     Run Docker container"
	@echo " clean          Clean cache files"

install:
	uv sync

run:
	granian --interface asgi --host 0.0.0.0 --port $(PORT) $(APP)

dev:
	granian --reload --interface asgi --host 0.0.0.0 --port $(PORT) $(APP)

lint:
	ruff check .

format:
	ruff format .

security:
	bandit -r app -ll

audit:
	pip-audit

trivy:
	trivy fs . --scanners vuln

docker-build:
	docker build -t py-scaffold .

docker-run:
	docker run -p 8000:8000 py-scaffold

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
