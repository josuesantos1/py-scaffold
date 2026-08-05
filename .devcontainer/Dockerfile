FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /workspace

RUN apt-get update && apt-get install -y make \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN groupadd -r scaffold && useradd -r -g scaffold -m -s /bin/bash scaffold

RUN pip install uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY . .

RUN chown -R scaffold:scaffold /workspace

USER scaffold

EXPOSE 1112

CMD ["granian", "--interface", "asgi", "--host", "0.0.0.0", "--port", "1112", "main:app"]
