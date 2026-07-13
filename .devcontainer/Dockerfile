FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /workspace

RUN apt-get update && apt-get install -y make \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN groupadd -r vscode && useradd -r -g vscode -m -s /bin/bash vscode

RUN pip install uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY . .

RUN chown -R vscode:vscode /workspace

USER vscode

EXPOSE 8000

CMD ["granian", "--interface", "asgi", "--host", "0.0.0.0", "--port", "8000", "main:app"]
