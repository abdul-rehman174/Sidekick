# --- Sidekick Pro v8.9 Dockerfile ---
FROM node:20-slim AS frontend-builder
WORKDIR /app/sidekick-frontend
COPY sidekick-frontend/package*.json ./
RUN npm install
COPY sidekick-frontend/ ./
RUN npm run build

FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

RUN useradd -m -u 1000 user
WORKDIR /home/user/app

USER root
RUN apt-get update && apt-get install -y \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

RUN chown -R user:user /home/user

USER user

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

COPY --chown=user . .
COPY --chown=user --from=frontend-builder /app/sidekick-frontend/dist ./static

RUN touch sidekick.db && chmod +x start.sh

EXPOSE 7860
CMD ["./start.sh"]
