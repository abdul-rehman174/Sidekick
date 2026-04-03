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

# Sidekick AI Pro (v8.8 Graduation) 🎓🛡️🏢🚀✨

**Sidekick AI Pro** is a production-grade, modular AI application that transforms a sassy/flirty personality into a highly structured and secure personal assistant. Built with **FastAPI**, **React**, and **Celery**, this version (v8.8) represents the final architectural graduation optimized for stability, security, and cloud deployment.

---

## 🫦 Key Features

- **Absolute Intent Gating (v8.3)**: Physically blocks tool-calling hallucinations. The AI only sees tools when a reminder intent is detected. 🚿🛡️
- **Physical De-Duplication Wall (v8.5)**: A 120-minute safety window and fuzzy-matching logic to ensure every reminder triggers **exactly once**. 🚫🔁
- **Usage & Token Monitoring (v8.6)**: Real-time tracking of prompt and completion tokens stored directly in the persistence layer. 📊🧪
- **Decoupled "Pro" Architecture**: The entire logic has been refactored into a clean, service-oriented `app/` package. 🎻
- **State-of-the-Art Security (JWT)**: Professional-grade authentication using SHA-256 signed bearer tokens. 🔒🛡️

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
│   ├── celery_app.py    # Background Task Orchestrator
│   ├── config.py        # Secure Environment Orchestration
│   └── database.py      # Persistence Configuration
├── sidekick-frontend/   # React/Vite Application
└── Dockerfile           # Multi-Stage Production Build
```

---

## 🛠 Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy, Gunicorn.
- **AI Engine**: Groq (Llama-3.3-70b-versatile).
- **Security**: Python-Jose (JWT), Passlib (BCrypt).
- **Background Tasks**: Celery, Redis.
- **Frontend**: React 18, Vite, TailwindCSS.

---

## 🚀 Deployment & Setup

### 1. Local Development
1. Install dependencies: `pip install -r requirements.txt`
2. Configure `.env`: Include your `GROQ_API_KEY`.
3. Start Redis: `redis-server`
4. Run Backend: `python main.py`
5. Start Worker: `celery -A app.celery_app worker -l info`
6. Start Frontend: `cd sidekick-frontend && npm run dev`

### 2. Cloud Deployment (Hugging Face / Docker) 🐳
The project is built for **Hugging Face Spaces** using a multi-stage `Dockerfile`. 
- **Internal Port**: 7860
- **SDK**: Docker

---

## 🤝 Professional Graduation
Sidekick AI Pro is designed with absolute package imports (`app.xxx`) and rigorous logic gating to ensure 100% stability in production environments. 

**Sidekick Pro (v8.8) — Engineered for stability, secured for privacy, and sassier than ever.** 🎓🛡️🏢🚀✨
