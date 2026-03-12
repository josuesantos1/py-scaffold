#!/usr/bin/env python3
"""Script to generate GitHub Actions CI workflow for an app."""

import argparse
import re
import sys
from pathlib import Path


def validate_app_name(app_name: str) -> None:
    """Validate app name follows Python naming conventions.

    Args:
        app_name: Name to validate

    Raises:
        SystemExit: If name is invalid
    """
    if not re.match(r"^[a-z][a-z0-9_]*$", app_name):
        print(f"✗ Error: Invalid app name '{app_name}'")
        print("  App name must:")
        print("  - Start with a lowercase letter")
        print("  - Contain only lowercase letters, digits, and underscores")
        print("  Examples: admin, user_auth, api_v2")
        sys.exit(1)


def create_ci_workflow(app_name: str, skip_validation: bool = False) -> None:
    """Create GitHub Actions CI workflow for the specified app.

    Args:
        app_name: Name of the application (e.g., 'admin', 'example')
        skip_validation: Skip app existence validation (default: False)
    """
    # Validate name
    validate_app_name(app_name)

    # Check if app exists
    if not skip_validation:
        app_dir = Path("app") / app_name
        if not app_dir.exists():
            print(f"✗ Error: App directory not found: {app_dir}")
            print(f"  Create the app first with: python manager.py create-app {app_name}")
            sys.exit(1)

    workflows_dir = Path(".github/workflows")
    workflows_dir.mkdir(parents=True, exist_ok=True)

    workflow_file = workflows_dir / f"{app_name}-ci.yml"

    workflow_content = f"""name: {app_name.capitalize()} App - CI

permissions:
  contents: read

concurrency:
  group: {app_name}-ci-${{{{ github.ref }}}}
  cancel-in-progress: true

on:
  push:
    branches: [main]
    paths:
      - 'app/{app_name}/**'
      - 'tests/{app_name}/**'
      - 'tests/test_{app_name}.py'
      - 'tests/conftest.py'
      - 'pyproject.toml'
      - 'uv.lock'
      - '.github/workflows/{app_name}-ci.yml'
  pull_request:
    branches: [main]
    paths:
      - 'app/{app_name}/**'
      - 'tests/{app_name}/**'
      - 'tests/test_{app_name}.py'
      - 'tests/conftest.py'
      - 'pyproject.toml'
      - 'uv.lock'
      - '.github/workflows/{app_name}-ci.yml'

jobs:
  lint-and-test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install uv
        uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - name: Install dependencies
        run: uv sync --frozen

      - name: Resolve test target
        id: tests
        shell: bash
        run: |
          if [ -d "tests/{app_name}" ]; then
            echo "target=tests/{app_name}" >> "$GITHUB_OUTPUT"
          elif [ -f "tests/test_{app_name}.py" ]; then
            echo "target=tests/test_{app_name}.py" >> "$GITHUB_OUTPUT"
          else
            echo "target=tests" >> "$GITHUB_OUTPUT"
          fi

      - name: Run Ruff lint
        run: uv run ruff check app/{app_name}

      - name: Run Ruff format check
        run: uv run ruff format --check app/{app_name}

      - name: Run Pyright
        run: uv run pyright app/{app_name}

      - name: Run Bandit security check
        run: uv run bandit -r app/{app_name} -ll

      - name: Run tests
        run: >
          uv run pytest ${{{{ steps.tests.outputs.target }}}} -v --cov=app/{app_name}
          --cov-report=term-missing --cov-fail-under=80
"""

    # Check if workflow already exists
    if workflow_file.exists():
        print(f"⚠ Warning: Workflow already exists: {workflow_file}")
        response = input("Overwrite? [y/N]: ")
        if response.lower() not in ("y", "yes"):
            print("✗ Aborted")
            sys.exit(0)

    try:
        workflow_file.write_text(workflow_content)
        print(f"✓ Created CI workflow: {workflow_file}")
    except OSError as e:
        print(f"✗ Error writing workflow file: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Create GitHub Actions CI workflow for an app")
    parser.add_argument("app_name", help="Name of the application (e.g., admin, example)")

    args = parser.parse_args()
    create_ci_workflow(args.app_name)


if __name__ == "__main__":
    main()
