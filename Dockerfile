# ============================================================
# Plinth — Multi-stage Docker build
# ============================================================
# Stage 1: Install dependencies with uv
# Stage 2: Slim runtime image
# ============================================================

# --- Build stage ---
FROM python:3.13-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies into a virtual environment
RUN uv sync --frozen --no-dev --no-install-project

# Copy source code
COPY src/ src/
COPY config.yaml .

# Install the project itself
RUN uv sync --frozen --no-dev

# --- Runtime stage ---
FROM python:3.13-slim AS runtime

LABEL maintainer="Rolex Alexander <rolexalexander67@gmail.com>"
LABEL description="Plinth — Turns discovery into a foundation downstream agents can build on"
LABEL org.opencontainers.image.source="https://github.com/yourusername/plinth"
LABEL org.opencontainers.image.license="MIT"

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application files
COPY --from=builder /app/src /app/src
COPY --from=builder /app/config.yaml /app/config.yaml
COPY --from=builder /app/pyproject.toml /app/pyproject.toml

# Copy default test transcript (can be overridden via volume mount)
COPY tests/sample_transcript.txt /app/tests/sample_transcript.txt

# Ensure output directory exists
RUN mkdir -p /app/output

# Add venv to PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Default entrypoint runs the flow
ENTRYPOINT ["python", "-m", "requirements_crew.main"]
CMD []
