#!/usr/bin/env python3
"""Project manager CLI — scaffold apps, workers, and CI workflows."""

from pathlib import Path

import typer
from rich.console import Console
from rich.tree import Tree

from scripts.create_ci import create_ci_workflow, validate_app_name

cli = typer.Typer(
    help="Project manager for py-scaffold.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


# ── Helpers ───────────────────────────────────────────────────────────────────


def _pascal(value: str) -> str:
    return "".join(part.capitalize() for part in value.split("_") if part)


def _abort(message: str) -> None:
    console.print(f"[bold red]✗[/] {message}")
    raise typer.Exit(1)


# ── Commands ──────────────────────────────────────────────────────────────────


@cli.command("list-apps")
def list_apps() -> None:
    """List all apps in the project."""
    app_dir = Path("app")
    if not app_dir.exists():
        _abort("app/ directory not found")

    apps = sorted(
        d.name
        for d in app_dir.iterdir()
        if d.is_dir() and not d.name.startswith(("__", "."))
    )

    if not apps:
        console.print("No apps found in [dim]app/[/]")
        return

    tree = Tree("[bold]app/[/]")
    for name in apps:
        tree.add(name)
    console.print(tree)


@cli.command("create-app")
def create_app(
    app_name: str = typer.Argument(..., help="App name in snake_case"),
    with_ci: bool = typer.Option(False, "--with-ci", help="Create CI workflow"),
    no_ci: bool = typer.Option(False, "--no-ci", help="Skip CI workflow prompt"),
) -> None:
    """Scaffold a new BlackSheep + asyncpg + msgspec app."""
    validate_app_name(app_name)

    app_dir = Path("app") / app_name
    tests_dir = Path("tests") / app_name
    model_name = _pascal(app_name)

    if app_dir.exists():
        _abort(f"App '{app_name}' already exists")

    try:
        app_dir.mkdir(parents=True)
        tests_dir.mkdir(parents=True)

        (app_dir / "__init__.py").touch()
        (tests_dir / "__init__.py").touch()

        (app_dir / "model.py").write_text(
            f'"""Data models for the {app_name} app.\n\n'
            "Uses msgspec.Struct — zero-copy JSON encode/decode, no ORM.\n"
            '"""\n\n'
            "import msgspec\n\n\n"
            f"class {model_name}Create(msgspec.Struct):\n"
            '    """Write schema — accepted in POST body."""\n\n'
            "    name: str\n\n\n"
            f"class {model_name}(msgspec.Struct, frozen=True, gc=False):\n"
            '    """Read model returned from the database."""\n\n'
            "    id: int\n"
            "    name: str\n\n\n"
            f"{app_name}_decoder = msgspec.json.Decoder({model_name}Create)\n",
            encoding="utf-8",
        )

        (app_dir / "service.py").write_text(
            f'"""Business logic for the {app_name} app.\n\n'
            "Functions accept an asyncpg.Connection directly — no ORM, no session.\n"
            '"""\n\n'
            "import asyncpg\n"
            "import structlog\n"
            "from opentelemetry import trace\n\n"
            f"from app.{app_name}.model import {model_name}, {model_name}Create\n\n"
            "logger = structlog.get_logger()\n"
            f'tracer = trace.get_tracer("app.{app_name}")\n\n\n'
            f"async def get_all(conn: asyncpg.Connection) -> list[{model_name}]:  "
            "# type: ignore[type-arg]\n"
            f'    """Return all {app_name} records ordered by id."""\n'
            f'    with tracer.start_as_current_span("db.get_all_{app_name}"):\n'
            "        rows = await conn.fetch(\n"
            f'            "SELECT id, name FROM {app_name} ORDER BY id"\n'
            "        )\n"
            f"    return [{model_name}(id=r[\"id\"], name=r[\"name\"]) for r in rows]\n",
            encoding="utf-8",
        )

        (app_dir / "view.py").write_text(
            f'"""HTTP handlers for the {app_name} app.\n\n'
            "Pattern:\n"
            "- Declare ``db: Database`` parameter — BlackSheep injects it per request.\n"
            "- Call ``async with db.connection() as conn:`` to acquire a DB connection.\n"
            '"""\n\n'
            "import structlog\n"
            "from blacksheep import Request, Response, Router\n\n"
            f"from app.{app_name} import service\n"
            f"from app.{app_name}.model import {app_name}_decoder\n"
            "from config.di import Database\n"
            "from config.responses import created, ok, unprocessable\n\n"
            f'PREFIX = "/v1/{app_name}"\n'
            f'TAGS = ["{app_name}"]\n\n'
            "logger = structlog.get_logger()\n\n"
            "router = Router(prefix=PREFIX)\n\n\n"
            "@router.get(\"/\")\n"
            f"async def list_{app_name}(db: Database) -> Response:\n"
            f"    async with db.connection() as conn:\n"
            f"        items = await service.get_all(conn)\n"
            "    return ok(items)\n\n\n"
            "@router.post(\"/\")\n"
            f"async def create_{app_name}(request: Request, db: Database) -> Response:\n"
            "    body = (await request.read()) or b\"\"\n"
            "    try:\n"
            f"        payload = {app_name}_decoder.decode(body)\n"
            "    except Exception as exc:\n"
            "        return unprocessable(str(exc))\n"
            f"    async with db.connection() as conn:\n"
            f"        item = await service.create_{app_name}(conn, payload)\n"
            "    return created(item)\n",
            encoding="utf-8",
        )

        (tests_dir / f"test_{app_name}.py").write_text(
            f'"""Tests for the {app_name} app.\n\n'
            "Uses the shared conftest fixtures:\n"
            "- client:    httpx AsyncClient against the full ASGI app\n"
            "- patch_db:  replaces config.database.get_db with a mock asyncpg connection\n"
            '"""\n\n'
            "from unittest.mock import AsyncMock\n\n"
            f"from app.{app_name} import service\n"
            f"from app.{app_name}.model import {model_name}\n\n\n"
            f"async def test_list_{app_name}_endpoint(client, patch_db, monkeypatch):\n"
            f'    fake_items = [{model_name}(id=1, name="example")]\n\n'
            "    async def fake_get_all(_conn):\n"
            "        return fake_items\n\n"
            f'    monkeypatch.setattr(service, "get_all", fake_get_all)\n\n'
            f'    response = await client.get("/v1/{app_name}/")\n'
            "    assert response.status_code == 200\n"
            "    assert isinstance(response.json(), list)\n\n\n"
            f"async def test_service_get_all_returns_items():\n"
            f'    rows = [{{"id": 1, "name": "example"}}]\n'
            "    conn = AsyncMock()\n"
            "    conn.fetch = AsyncMock(return_value=rows)\n\n"
            "    result = await service.get_all(conn)\n\n"
            "    assert len(result) == 1\n"
            f'    assert result[0] == {model_name}(id=1, name="example")\n'
            "    conn.fetch.assert_awaited_once()\n",
            encoding="utf-8",
        )

    except OSError as exc:
        _abort(f"Error creating app structure: {exc}")

    tree = Tree(f"[bold green]✓[/] Created [bold]{app_name}[/]")
    app_branch = tree.add(f"[dim]app/{app_name}/[/]")
    for f in ("__init__.py", "model.py", "service.py", "view.py"):
        app_branch.add(f)
    test_branch = tree.add(f"[dim]tests/{app_name}/[/]")
    test_branch.add(f"test_{app_name}.py")
    console.print(tree)
    console.print(
        f"\n[dim]Router auto-discovered at prefix[/] [cyan]/v1/{app_name}[/]\n"
        f"[dim]No changes needed in main.py.[/]\n"
    )

    if with_ci or (
        not no_ci
        and typer.confirm(f"\nCreate GitHub Actions CI workflow for '{app_name}'?", default=True)
    ):
        create_ci_workflow(app_name, skip_validation=True)


@cli.command("create-ci")
def create_ci(
    app_name: str = typer.Argument(..., help="Name of the app"),
) -> None:
    """Create a GitHub Actions CI workflow for an existing app."""
    create_ci_workflow(app_name)


@cli.command("create-worker")
def create_worker(
    worker_name: str = typer.Argument(..., help="Worker name in snake_case"),
    subject: str = typer.Option(..., "--subject", help="NATS subject (e.g. scraper.execute)"),
) -> None:
    """Scaffold a NATS JetStream worker."""
    validate_app_name(worker_name)

    worker_dir = Path("workers") / worker_name
    tests_dir = Path("tests") / "workers" / worker_name

    if worker_dir.exists():
        _abort(f"Worker '{worker_name}' already exists")

    try:
        worker_dir.mkdir(parents=True)
        tests_dir.mkdir(parents=True)

        (worker_dir / "__init__.py").touch()
        (tests_dir / "__init__.py").touch()

        tests_workers_init = Path("tests") / "workers" / "__init__.py"
        if not tests_workers_init.exists():
            tests_workers_init.touch()

        (worker_dir / "handler.py").write_text(
            f'"""Message handler for the {worker_name} worker."""\n\n'
            "import structlog\n\n"
            "logger = structlog.get_logger()\n\n\n"
            "async def handle(payload: dict) -> None:  # type: ignore[type-arg]\n"
            f'    """Process a message from subject \'{subject}\'."""\n'
            f'    logger.info("{worker_name}.handle", payload=payload)\n'
            "    # TODO: implement handler logic\n",
            encoding="utf-8",
        )

        (worker_dir / "worker.py").write_text(
            f'"""NATS JetStream consumer for {worker_name}."""\n\n'
            "import asyncio\n\n"
            "import orjson\n"
            "import structlog\n"
            "from nats.aio.msg import Msg\n\n"
            "from config.log import setup_logging\n"
            "from config.nats import connect, setup_streams\n"
            f"from workers.{worker_name}.handler import handle\n\n"
            "logger = structlog.get_logger()\n\n"
            f'SUBJECT = "{subject}"\n'
            f'CONSUMER = "{worker_name}"\n\n\n'
            "async def _on_message(msg: Msg) -> None:\n"
            "    try:\n"
            "        payload = orjson.loads(msg.data)\n"
            "        await handle(payload)\n"
            "        await msg.ack()\n"
            "    except Exception as exc:\n"
            f'        logger.error("{worker_name}.error", error=str(exc))\n'
            "        await msg.nak()\n\n\n"
            "async def run() -> None:\n"
            "    setup_logging()\n"
            "    nc = await connect()\n"
            "    js = await setup_streams(nc)\n"
            "    await js.subscribe(SUBJECT, durable=CONSUMER, cb=_on_message)\n"
            f'    logger.info("{worker_name}.started", subject=SUBJECT)\n'
            "    try:\n"
            "        await asyncio.Future()\n"
            "    finally:\n"
            "        await nc.drain()\n\n\n"
            'if __name__ == "__main__":\n'
            "    asyncio.run(run())\n",
            encoding="utf-8",
        )

        (tests_dir / f"test_{worker_name}.py").write_text(
            f'"""Tests for the {worker_name} worker."""\n\n'
            "from unittest.mock import AsyncMock, patch\n\n"
            "import orjson\n\n"
            f"from workers.{worker_name} import worker as {worker_name}_worker\n"
            f"from workers.{worker_name}.handler import handle\n\n\n"
            "async def test_handle_runs_without_error():\n"
            '    await handle({"job_id": "test-id"})\n\n\n'
            "async def test_on_message_acks_on_success():\n"
            "    msg = AsyncMock()\n"
            '    msg.data = orjson.dumps({"job_id": "test-id"})\n\n'
            f"    await {worker_name}_worker._on_message(msg)\n\n"
            "    msg.ack.assert_awaited_once()\n"
            "    msg.nak.assert_not_awaited()\n\n\n"
            "async def test_on_message_naks_on_error():\n"
            "    msg = AsyncMock()\n"
            '    msg.data = orjson.dumps({"job_id": "test-id"})\n\n'
            "    with patch(\n"
            f'        "workers.{worker_name}.worker.handle",\n'
            '        AsyncMock(side_effect=RuntimeError("boom")),\n'
            "    ):\n"
            f"        await {worker_name}_worker._on_message(msg)\n\n"
            "    msg.nak.assert_awaited_once()\n"
            "    msg.ack.assert_not_awaited()\n",
            encoding="utf-8",
        )

    except OSError as exc:
        _abort(f"Error creating worker structure: {exc}")

    tree = Tree(f"[bold green]✓[/] Created worker [bold]{worker_name}[/]")
    w_branch = tree.add(f"[dim]workers/{worker_name}/[/]")
    for f in ("__init__.py", "handler.py", "worker.py"):
        w_branch.add(f)
    t_branch = tree.add(f"[dim]tests/workers/{worker_name}/[/]")
    t_branch.add(f"test_{worker_name}.py")
    console.print(tree)
    console.print(f"\n  Subject : [cyan]{subject}[/]")
    console.print(f"  Consumer: [cyan]{worker_name}[/]")
    console.print(f"\n  Run with: [dim]uv run python -m workers.{worker_name}.worker[/]\n")


if __name__ == "__main__":
    cli()
