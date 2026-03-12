#!/usr/bin/env python3
"""Project manager script for common development tasks."""

import argparse
import sys
from pathlib import Path

from scripts.create_ci import create_ci_workflow, validate_app_name


def to_pascal_case(value: str) -> str:
    """Convert snake_case names to PascalCase."""
    return "".join(part.capitalize() for part in value.split("_") if part)


def list_apps() -> None:
    """List all available apps in the project."""
    app_dir = Path("app")
    if not app_dir.exists():
        print("✗ Error: app/ directory not found")
        sys.exit(1)

    apps = [
        d.name
        for d in app_dir.iterdir()
        if d.is_dir() and not d.name.startswith("__") and not d.name.startswith(".")
    ]

    if apps:
        print("Available apps:")
        for app in sorted(apps):
            print(f"  • {app}")
    else:
        print("No apps found in app/ directory")


def create_app(app_name: str, with_ci: bool = False, no_ci: bool = False) -> None:
    """Create a new app structure.

    Args:
        app_name: Name of the application to create
        with_ci: Automatically create CI workflow (default: False)
        no_ci: Skip CI workflow creation (default: False)
    """
    # Validate name
    validate_app_name(app_name)

    app_dir = Path("app") / app_name
    tests_dir = Path("tests") / app_name
    model_name = to_pascal_case(app_name)

    if app_dir.exists():
        print(f"✗ Error: App '{app_name}' already exists")
        sys.exit(1)

    try:
        # Create app directories
        app_dir.mkdir(parents=True)
        tests_dir.mkdir(parents=True)

        # Create __init__.py files
        (app_dir / "__init__.py").touch()
        (tests_dir / "__init__.py").touch()

        # Create model.py
        (app_dir / "model.py").write_text(
            f'"""Models for {app_name} app."""\n\n'
            "from sqlmodel import Field, SQLModel\n\n\n"
            f"class {model_name}(SQLModel, table=True):\n"
            '    """TODO: Define your model."""\n'
            "    id: int | None = Field(default=None, primary_key=True)\n"
            "    name: str\n\n\n"
            f"class {model_name}Create(SQLModel):\n"
            '    """Schema for creating new records."""\n'
            "    name: str\n"
        )

        # Create service.py
        (app_dir / "service.py").write_text(
            f'"""Business logic for {app_name} app."""\n\n'
            "import structlog\n"
            "from sqlmodel import select\n"
            "from sqlmodel.ext.asyncio.session import AsyncSession\n\n"
            f"from app.{app_name}.model import {model_name}\n\n"
            "logger = structlog.get_logger()\n\n\n"
            f"async def get_all(session: AsyncSession) -> list[{model_name}]:\n"
            f'    """Get all {app_name} records."""\n'
            f"    result = await session.exec(select({model_name}))\n"
            "    return result.all()\n"
        )

        # Create view.py
        (app_dir / "view.py").write_text(
            f'"""Views for {app_name} app."""\n\n'
            "import structlog\n"
            "from fastapi import APIRouter, Depends\n"
            "from sqlmodel.ext.asyncio.session import AsyncSession\n\n"
            f"from app.{app_name} import service\n"
            f"from app.{app_name}.model import {model_name}\n"
            "from config.database import get_db\n\n"
            "logger = structlog.get_logger()\n\n"
            "router = APIRouter()\n\n\n"
            f'@router.get("/", response_model=list[{model_name}])\n'
            "async def list_items(session: AsyncSession = Depends(get_db)):\n"
            f'    """List all {app_name} items."""\n'
            "    return await service.get_all(session)\n"
        )

        # Create test file
        (tests_dir / f"test_{app_name}.py").write_text(
            f'"""Tests for {app_name} app."""\n\n'
            f"def test_{app_name}_placeholder() -> None:\n"
            '    """Placeholder test - replace with actual tests."""\n'
            "    assert True\n"
        )

        print("✓ Created app structure:")
        print(f"  • {app_dir}/")
        print("    - __init__.py")
        print("    - model.py")
        print("    - service.py")
        print("    - view.py")
        print(f"  • {tests_dir}/")
        print(f"    - test_{app_name}.py")

    except OSError as e:
        print(f"✗ Error creating app structure: {e}")
        sys.exit(1)

    # Handle CI workflow creation
    if with_ci:
        create_ci_workflow(app_name, skip_validation=True)
    elif not no_ci:
        response = input(f"\nCreate GitHub Actions CI workflow for '{app_name}'? [Y/n]: ")
        if response.lower() in ("", "y", "yes"):
            create_ci_workflow(app_name, skip_validation=True)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Project manager for py-scaffold",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  manager.py list-apps              List all apps
  manager.py create-app myapp       Create new app structure
  manager.py create-ci myapp        Create CI workflow for app
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # list-apps command
    subparsers.add_parser("list-apps", help="List all available apps")

    # create-app command
    create_app_parser = subparsers.add_parser("create-app", help="Create new app structure")
    create_app_parser.add_argument("app_name", help="Name of the app to create")
    create_app_parser.add_argument(
        "--with-ci", action="store_true", help="Automatically create CI workflow"
    )
    create_app_parser.add_argument(
        "--no-ci", action="store_true", help="Skip CI workflow creation"
    )

    # create-ci command
    create_ci_parser = subparsers.add_parser("create-ci", help="Create CI workflow for an app")
    create_ci_parser.add_argument("app_name", help="Name of the app")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "list-apps":
        list_apps()
    elif args.command == "create-app":
        create_app(args.app_name, with_ci=args.with_ci, no_ci=args.no_ci)
    elif args.command == "create-ci":
        create_ci_workflow(args.app_name)


if __name__ == "__main__":
    main()
