#!/bin/sh
set -e

echo "[entrypoint] Starting Editorial Workspace Production Container..."

# Run database migrations if configured
if [ "$RUN_MIGRATIONS" != "false" ]; then
    echo "[entrypoint] Running database migrations (alembic upgrade head)..."
    alembic -c backend/alembic.ini upgrade head || {
        echo "[entrypoint] Warning: Alembic upgrade encountered an issue or was skipped."
    }
fi

PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"
WORKERS="${WORKERS:-2}"

echo "[entrypoint] Launching application on ${HOST}:${PORT} with ${WORKERS} worker(s)..."
exec uvicorn backend.app.main:app --host "${HOST}" --port "${PORT}" --workers "${WORKERS}" "$@"

