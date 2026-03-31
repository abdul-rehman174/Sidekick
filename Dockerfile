# --- STAGE 1: Build Frontend ---
FROM node:20-slim AS frontend-builder
WORKDIR /app/sidekick-frontend
COPY sidekick-frontend/package*.json ./
RUN npm install
COPY sidekick-frontend/ ./
RUN npm run build

# --- STAGE 2: Build Backend & Run ---
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies (needed for some python packages)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Copy the built frontend from STAGE 1
# We put it where FastAPI expects it (based on main.py)
RUN mkdir -p sidekick-frontend/dist
COPY --from=frontend-builder /app/sidekick-frontend/dist ./sidekick-frontend/dist

# Make start script executable
RUN chmod +x start.sh

# Expose the port FastAPI runs on
EXPOSE 8000

# Start the application using our helper script
CMD ["./start.sh"]
