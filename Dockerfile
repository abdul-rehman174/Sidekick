FROM node:20-slim AS frontend-builder
WORKDIR /app/sidekick-frontend
COPY sidekick-frontend/package*.json ./
RUN npm ci
COPY sidekick-frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

RUN useradd -m -u 1000 user
WORKDIR /home/user/app

USER user
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

COPY --chown=user app ./app
COPY --chown=user main.py start.sh ./
COPY --chown=user --from=frontend-builder /app/sidekick-frontend/dist ./static

RUN chmod +x start.sh

EXPOSE 7860
CMD ["./start.sh"]
