FROM mcr.microsoft.com/devcontainers/python:3.13

RUN apt-get update && apt-get install -y \
    curl \
    git \
    make \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# instalar uv globalmente
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# ferramentas de dev
RUN pip install \
    ruff \
    bandit \
    pip-audit \
    granian

# instalar trivy
RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \
    | sh -s -- -b /usr/local/bin

WORKDIR /workspace