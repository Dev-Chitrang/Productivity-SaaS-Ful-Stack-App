# =============================================================================
# Stage 1: Builder — install dependencies with compile support
# =============================================================================
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 1. Install GCC and compilation tools needed for packages like multidict
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .

# 2. Use PIP to install your dependencies ultra-fast inside the virtual environment
RUN pip install --no-cache -r requirements.txt


# =============================================================================
# Stage 2: Runtime — minimal production image (Remains clean and light)
# =============================================================================
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends libmagic1 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 appuser \
    && useradd  --uid 1000 --gid 1000 --no-create-home --shell /bin/false appuser

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY alembic.ini .
COPY alembic/ alembic/
COPY app/ app/
COPY entrypoint.sh .
COPY celery_entrypoint.sh .

RUN mkdir -p /app/downloads /app/logs \
    && chown -R appuser:appuser /app/downloads /app/logs \
    && chmod +x /app/entrypoint.sh /app/celery_entrypoint.sh

RUN find /app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; \
    find /app -name "*.pyc" -delete 2>/dev/null; \
    true

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--proxy-headers", "--forwarded-allow-ips", "*"]
