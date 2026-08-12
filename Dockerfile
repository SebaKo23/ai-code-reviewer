FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-cache

COPY STYLEGUIDE.md ./
COPY src/ ./src/

CMD ["uv", "run", "python", "-m", "src.github_app"]