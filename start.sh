#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting Sidekick Application..."

# 1. Start Celery Worker in the background
# We use -A celery_app to point to our celery instance
echo "🕒 Starting Celery Worker..."
celery -A celery_app worker --loglevel=info &

# 2. Start FastAPI with Gunicorn (Production server)
# --workers 1 since free tiers are small
# --worker-class uvicorn.workers.UvicornWorker to handle async
echo "🌐 Starting FastAPI Server..."
gunicorn main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Wait for all background processes to finish
wait
