# Py-Scaffold

Modern Python API scaffold with FastAPI, SQLAlchemy, Alembic, and comprehensive tooling.

## Features

- **FastAPI** - Modern, fast web framework
- **SQLAlchemy 2.0** - Async ORM with Alembic migrations
- **Granian** - High-performance ASGI server
- **Structured Logging** - JSON logging with structlog
- **Metrics** - Prometheus metrics built-in
- **Security** - Bandit, pip-audit, Trivy scanning
- **Code Quality** - Ruff (linting + formatting), Pyright (type checking)
- **Testing** - pytest with async support and coverage
- **DevContainer** - Ready-to-use development environment

## Quick Start

### Development (DevContainer - Recommended)

1. Open in VSCode
2. Click "Reopen in Container"
3. Dependencies install automatically via `postStartCommand`
4. Run: `make dev`

### Local Development

```bash
# Install dependencies
make install

# Copy environment file (Linux/macOS)
cp .env.example .env

# Copy environment file (Windows PowerShell)
Copy-Item .env.example .env

# Run in development mode
make dev
```

## Available Commands

```bash
make install        # Install dependencies
make run            # Run API in production mode
make dev            # Run API with hot reload
make lint           # Run Ruff linter
make format         # Format code with Ruff
make fix            # Auto-fix lint issues and format
make typecheck      # Run Pyright type checker
make security       # Run Bandit security scan
make audit          # Run pip-audit for vulnerabilities
make test           # Run tests with coverage (80% minimum)
make check          # Run all checks (lint + typecheck + security + audit + test)
make trivy          # Scan with Trivy
make clean          # Clean cache files
make ci             # Run check + trivy
```

## Project Structure

```
.
├── app/                  # Application modules
│   ├── admin/
│   ├── example/
│   └── teste/
├── config/               # Configuration
│   ├── database.py       # Database session/engine
│   ├── exceptions.py     # Exception handlers
│   ├── log.py            # Structured logging setup
│   ├── metrics.py        # Prometheus collectors
│   └── settings.py       # Pydantic settings
├── migrations/           # Alembic migrations
├── tests/                # Test suite
├── main.py               # FastAPI entrypoint
├── manager.py            # App/CI scaffolding helper
├── Makefile              # Development commands
└── pyproject.toml        # Dependencies and tool config
```

## Configuration

All configuration is managed via environment variables using pydantic-settings.

Copy `.env.example` to `.env` and adjust:

```bash
# App
APP_NAME=Py-Scaffold API
DEBUG=false

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname

# CORS (comma-separated)
CORS_ORIGINS=*

# Logging
LOG_LEVEL=INFO
```

## Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Endpoints

- `GET /admin/health` - Health check
- `GET /admin/ready` - Readiness probe
- `GET /admin/metrics` - Prometheus metrics
- `GET /docs` - OpenAPI documentation

## Testing

```bash
# Run tests
make test

# Run tests with verbose output
uv run pytest -v

# Run specific test
uv run pytest tests/test_health.py
```

## CI/CD

The project includes a `make ci` command that runs all checks:

```bash
make ci  # Runs: lint, typecheck, security, audit, test, trivy
```

## Security Scanning

Multiple layers of security scanning:

- **Bandit** - Python code security issues
- **pip-audit** - Dependency vulnerabilities
- **Trivy** - Comprehensive vulnerability scanning
- **Ruff** - Security-related linting rules (S prefix)

## License

