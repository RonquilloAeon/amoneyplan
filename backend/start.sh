#!/usr/bin/env bash
# Exit on error
set -o errexit

cd src

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate

# Start Uvicorn using exec
exec uvicorn amoneyplan.asgi:application --host 0.0.0.0 --port "${PORT:-10000}"
