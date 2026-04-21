---
title: Sidekick AI Pro
emoji: 🫦
colorFrom: pink
colorTo: purple
sdk: docker
app_port: 7860
pinned: true
license: mit
---

# Sidekick AI Pro (v9.0 Professional Edition) 🎓🛡️🏢🚀✨

**Sidekick AI Pro** is a highly optimized, enterprise-grade AI application. Building upon its predecessors, version 9.0 introduces a totally asynchronous architecture, rendering slow blocks extinct. Built with **FastAPI**, **React**, and **aiosqlite**, this version represents a clean leap forward in performance, decoupled architecture, and scalable design.

---

## 🫦 Key Features

- **Asynchronous Execution**: Fully migrated to `AsyncGroq` and `aiosqlite` connected to an async `SQLAlchemy 2.0` infrastructure to support massive horizontal scaling and zero-blocking routes. 🚀
- **Strict Pydantic Validation**: Bulletproof environment configuration (`pydantic-settings`) ensuring absolute boot safety. 🛡️
- **Professional Modularity**: The `AIService` has been abstracted into localized functions separating pure IO tasks (Inference) from Database handling/Tool extractions. 🎻
- **State-of-the-Art Security (JWT)**: Professional-grade authentication using SHA-256 signed bearer tokens with exact session dependencies. 🔒🛡️

---

## 📁 System Architecture

```text
/
├── main.py              # Root Entrypoint (Modular Delegation)
├── app/                 # The Hardened Backend Core
│   ├── routes/          # API Routers (chat, reminders, users)
│   ├── services/        # Business Logic (AIService, ReminderService)
│   ├── models/          # SQLAlchemy Metrics Schema
│   ├── auth/            # JWT Security & Auth Logic
│   ├── exceptions.py    # Custom Exception Handlers 
│   ├── config.py        # Secure Pydantic Settings
│   └── database.py      # Async db drivers & context managers
├── sidekick-frontend/   # React/Vite Application
├── tests/               # Pytest Suite
└── Dockerfile           # Multi-Stage Production Build
```

---

## 🛠 Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy (Async), Gunicorn.
- **AI Engine**: Groq (Llama-3.3-70b-versatile via `AsyncGroq`).
- **Security**: Python-Jose (JWT), Passlib (BCrypt).
- **Frontend**: React 18, Vite, TailwindCSS.

---

## 🚀 Deployment & Setup

### 1. Local Development
1. Install dependencies: `pip install -r requirements.txt` (or via `./sidevenv/bin/pip`)
2. Configure `.env`: Include your `GROQ_API_KEY`.
3. Run Local Tests: `pytest tests/`
4. Run Backend: `python main.py`
5. Start Frontend: `cd sidekick-frontend && npm run dev`

### 2. Cloud Deployment (Hugging Face / Docker) 🐳
The project is built for **Hugging Face Spaces** using a multi-stage `Dockerfile`. 
- **Internal Port**: 7860
- **SDK**: Docker

---

## 🤝 Clean Code Pledge
Sidekick AI Pro is designed with absolute package imports (`app.xxx`), asynchronous database contexts, and rigorously decoupled logic gateways. No Celery. No Redis. Just pure, rapid Python performance.

**Sidekick Pro (v9.0) — Engineered for massive scale, secured for privacy.** 🎓🛡️🏢🚀✨