# ==============================================================================
# WorkVision AI — Unified Container Image for Workspace Applications
# ==============================================================================

FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS base

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Copy dependency specifications
COPY pyproject.toml uv.lock ./
COPY packages/ ./packages/
COPY apps/ ./apps/

# Install workspace packages & dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

# Default entrypoint
CMD ["uvicorn", "workvision_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
