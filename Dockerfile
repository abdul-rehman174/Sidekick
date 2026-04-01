# --- STAGE 1: Build Frontend (Layer Cached) ---
FROM node:20-slim AS frontend-builder
WORKDIR /app/sidekick-frontend
# Only copy package files first for faster npm install caching
COPY sidekick-frontend/package*.json ./
RUN npm install
# Now copy the rest and build
COPY sidekick-frontend/ ./
RUN npm run build

# --- STAGE 2: Backend (Layer Cached) ---
FROM python:3.11-slim
WORKDIR /app

# Install only what we basic need
RUN apt-get update && apt-get install -y \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

# Install requirements (Cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Copy the built frontend
COPY --from=frontend-builder /app/sidekick-frontend/dist ./sidekick-frontend/dist

# Ensure script is ready
RUN chmod +x start.sh

# HF Default Port
EXPOSE 7860

CMD ["./start.sh"]
