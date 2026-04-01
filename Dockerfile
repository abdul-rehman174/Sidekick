# --- STAGE 1: Build Frontend (Layer Cached) ---
FROM node:20-slim AS frontend-builder
WORKDIR /app/sidekick-frontend
COPY sidekick-frontend/package*.json ./
RUN npm install
COPY sidekick-frontend/ ./
RUN npm run build

# --- STAGE 2: Backend (Layer Cached) ---
FROM python:3.11-slim

# 1. Create a non-root user (Hugging Face requirement)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
	PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# 2. Install system dependencies (Redis)
USER root
RUN apt-get update && apt-get install -y \
    redis-server \
    && rm -rf /var/lib/apt/lists/*
USER user

# 3. Install Python requirements
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 4. Copy backend code and built frontend
COPY --chown=user . .
COPY --chown=user --from=frontend-builder /app/sidekick-frontend/dist ./sidekick-frontend/dist

# 5. Prepare database file with correct ownership
RUN touch sidekick.db

# 6. Make start script executable
RUN chmod +x start.sh

# 7. Expose HF port
EXPOSE 7860

CMD ["./start.sh"]
