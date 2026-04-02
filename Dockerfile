# --- STAGE 1: Build Frontend ---
FROM node:20-slim AS frontend-builder
WORKDIR /app/sidekick-frontend
COPY sidekick-frontend/package*.json ./
RUN npm install
COPY sidekick-frontend/ ./
RUN npm run build

# --- STAGE 2: Backend & Runtime ---
FROM python:3.11-slim

# Professional standard: disable byte-code & enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Create a non-root user for security
RUN useradd -m -u 1000 user
WORKDIR $HOME/app

# Install system dependencies (Redis for All-In-One capability)
USER root
RUN apt-get update && apt-get install -y \
    redis-server \
    && rm -rf /var/lib/apt/lists/*
USER user

# Install Python requirements
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy backend source code
COPY --chown=user . .

# [PRO ARCHITECTURE]: Copy production frontend assets to /static
COPY --chown=user --from=frontend-builder /app/sidekick-frontend/dist ./static

# Ensure persistent storage exists and is writable
RUN touch sidekick.db && chmod +x start.sh

# Default Sidekick Port
EXPOSE 7860

# Launch through professional start script
CMD ["./start.sh"]
