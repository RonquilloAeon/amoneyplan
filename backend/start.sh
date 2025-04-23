#!/usr/bin/env bash
# Exit on error
set -o errexit

# Collect static files
python src/manage.py collectstatic --no-input

# Apply database migrations
python src/manage.py migrate

# Start Uvicorn using exec
exec uvicorn amoneyplan.asgi:application --host 0.0.0.0 --port "${PORT:-8000}"
