#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting Sidekick Application (All-In-One Mode)..."

# 1. Start Redis Server (the clipboard)
echo "📦 Starting Local Redis Server..."
redis-server --daemonize yes

# 2. Wait a moment for Redis to wake up
sleep 2

# 3. Start Celery Worker (the alarm clock)
echo "🕒 Starting Celery Worker..."
celery -A celery_app worker --loglevel=info &

# 4. Start FastAPI with Gunicorn (the brain)
# Bind to 7860 for Hugging Face Spaces compatibility
echo "🌐 Starting FastAPI Server on port 7860..."
gunicorn main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:7860

# Wait for all background processes to finish
wait
