# Py-Scaffold

High-performance Python API scaffold: BlackSheep + Granian + AsyncPG + msgspec.

## Stack

| Layer | Library |
| --- | --- |
| Framework | BlackSheep 2.x |
| Server | Granian (ASGI, multi-worker) |
| Database | asyncpg (raw SQL, no ORM) |
| Serialisation | msgspec (zero-copy JSON) |
| Migrations | Alembic |
| Logging | structlog (JSON) |
| Metrics | prometheus-client |
| Tracing | OpenTelemetry |
| DI | rodi (BlackSheep built-in) |

## Quick Start

### DevContainer (recommended)

```bash
# 1. Start infrastructure services
make services-up

# 2. Open in VS Code → "Reopen in Container"
#    Postgres + API start automatically.

# 3. Inside the container
uv run alembic upgrade head
make dev
```

### Local

```bash
make install
make services-up          # postgres on :5432
uv run alembic upgrade head
make dev                  # API on :1112 with reload
```

## Commands

```bash
make install          Install dependencies
make run              Run API (multi-worker, auto workers)
make dev              Run API with hot reload
make lint             Ruff lint
make format           Ruff format
make fix              Auto-fix lint + format
make typecheck        Pyright
make security         Bandit
make audit            pip-audit
make vulture          Dead code check
make test             pytest + coverage (≥ 80 %)
make check            lint + typecheck + security + audit + vulture + test
make trivy            Trivy vulnerability scan
make ci               check + trivy
make clean            Remove cache files
```

### Infrastructure

```bash
make services-up      Start postgres (creates infra_backend network)
make services-down    Stop postgres
make services-logs    Follow postgres logs
make nginx-up         Start nginx reverse proxy
make nginx-down       Stop nginx
make prometheus-up    Start Prometheus
make prometheus-down  Stop Prometheus
```

### Load Tests

```bash
make k6-smoke         1 VU · 30 s  — sanity check (runs in CI on every push)
make k6-load          50 VUs · 5 m — normal production simulation
make k6-stress        up to 300 VUs — find the breaking point
make k6-soak          20 VUs · 13 m — leak / pool exhaustion detection
make benchmark        pytest msgspec micro-benchmarks
```

Override the target URL:

```bash
K6_BASE_URL=http://staging:1112 make k6-load
```

## Project Structure

```text
.
├── app/
│   ├── admin/            health, ready, metrics endpoints
│   └── example/          example CRUD app (items)
├── config/
│   ├── database.py       asyncpg pool + get_db context manager
│   ├── di.py             Database injectable (rodi)
│   ├── exceptions.py     AppException + handlers
│   ├── log.py            structlog JSON setup
│   ├── metrics.py        Prometheus collectors
│   ├── responses.py      pre-built response helpers
│   └── settings.py       msgspec Settings (env vars)
├── infra/
│   ├── nginx/            nginx.conf
│   ├── prometheus/       prometheus.yml
│   └── services/
│       ├── postgres/     docker-compose.yml (creates infra_backend network)
│       ├── nginx/        docker-compose.yml (joins infra_backend)
│       └── prometheus/   docker-compose.yml (joins infra_backend)
├── load-tests/
│   └── k6/
│       ├── lib/helpers.js  shared checks, thresholds, randomItem()
│       ├── smoke.js
│       ├── load.js
│       ├── stress.js
│       └── soak.js
├── migrations/           Alembic migrations
├── prod/                 Production Dockerfile
├── tests/
│   ├── benchmarks/       msgspec encode/decode benchmarks
│   ├── conftest.py       shared fixtures (client, patch_db)
│   ├── test_example.py   unit + view tests
│   ├── test_integration.py full ASGI stack tests
│   └── test_settings.py
├── workers/              NATS JetStream workers (scaffolded)
├── main.py               ASGI entry point + auto-discovery router
├── manager.py            CLI scaffold (create-app, create-worker, create-ci)
├── Makefile
└── pyproject.toml
```

## Auto-discovery Routing

Any `app/<name>/view.py` that exports `PREFIX` and `router` is mounted automatically — no changes to `main.py` required:

```python
PREFIX = "/v1/items"
TAGS   = ["items"]
router = Router(prefix=PREFIX)
```

## Dependency Injection

Route handlers declare `db: Database` and BlackSheep injects it per request:

```python
@router.get("/")
async def list_items(db: Database) -> Response:
    async with db.connection() as conn:
        items = await service.get_items(conn)
    return ok(items)
```

## Scaffolding

```bash
# New app — auto-discovers router, prompts for CI workflow
uv run python manager.py create-app payments

# New NATS worker — prompts for CI workflow
uv run python manager.py create-worker invoice --subject billing.invoice

# Generate CI workflow for an existing app or worker
uv run python manager.py create-ci payments
```

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/admin/health` | Health check |
| GET | `/admin/ready` | Readiness probe |
| GET | `/admin/metrics` | Prometheus metrics |
| GET | `/v1/items/` | List items |
| GET | `/v1/items/{id}` | Get item |
| POST | `/v1/items/` | Create item |

## CI Workflows

Each app and worker gets its own workflow under `.github/workflows/` that triggers **only on changes to that module**:

| Workflow | Trigger paths |
| --- | --- |
| `core-ci.yml` | `main.py`, `config/**`, `migrations/**` |
| `{name}-ci.yml` | `app/{name}/**`, `tests/test_{name}.py` |
| `{name}-worker-ci.yml` | `workers/{name}/**`, `tests/workers/{name}/**` |
| `k6.yml` | `load-tests/**`, `app/**` — smoke on push, any scenario via `workflow_dispatch` |

## Configuration

All settings are read from environment variables via msgspec:

```bash
APP_NAME=Py-Scaffold API
DEBUG=false
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
CORS_ORIGINS=*
LOG_LEVEL=INFO
```

## Database Migrations

```bash
alembic revision --autogenerate -m "add items table"
alembic upgrade head
alembic downgrade -1
```

## Security

| Tool | Scope |
| --- | --- |
| Bandit | Python source (SAST) |
| pip-audit | Dependency CVEs |
| Trivy | Full filesystem + container |
| detect-secrets | Secret scanning (pre-commit) |
| Ruff S-rules | Security linting |
