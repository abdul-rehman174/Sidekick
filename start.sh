#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting Sidekick Application (Hugging Face Mode)..."

# Start FastAPI with Gunicorn (the brain)
# Bind to 7860 for Hugging Face Spaces compatibility
echo "🌐 Starting FastAPI Server on port 7860..."
gunicorn main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:7860

# Wait for all background processes to finish
wait
