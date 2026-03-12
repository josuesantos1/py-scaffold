# builder
FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

# runner
FROM python:3.13-slim AS runtime

RUN groupadd -r app && useradd -r -g app -d /app app

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY app/        ./app/
COPY config/     ./config/
COPY migrations/ ./migrations/
COPY main.py     ./

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER app

EXPOSE 8000

CMD ["granian", "--interface", "asgi", "--host", "0.0.0.0", "--port", "8000", "main:app"]
