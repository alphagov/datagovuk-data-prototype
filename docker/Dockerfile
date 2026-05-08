FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS python

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl git \
    && rm -rf /var/lib/apt/lists/* \
    && curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to /usr/local/bin

WORKDIR /app
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --dev --no-install-project

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --dev

RUN chmod +x docker/entrypoint.sh

EXPOSE 5050
ENTRYPOINT ["/bin/sh", "docker/entrypoint.sh"]
CMD ["uv", "run", "flask", "run", "--host=0.0.0.0", "--port=5050"]
