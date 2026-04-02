# Sidekick AI Pro (v7.5) 🛡️🏢🚀✨

**Sidekick AI Pro** is a production-grade, modular AI application that transforms a sassy/flirty personality into a highly structured and secure personal assistant. Built with **FastAPI**, **React**, and **Celery**, this version (v7.5) represents a full architectural refactor designed for stability, security, and scalability.

---

## 🫦 Key Features

- **Decoupled "Pro" Architecture**: The entire logic has been refactored into a clean, service-oriented `app/` package. 🎻
- **State-of-the-Art Security (JWT)**: Replaced insecure header-based ID passing with **JSON Web Tokens**. All private endpoints are protected by cryptographically signed bearer tokens. 🔒
- **Formal AI Tool Orchestration**: Reminders are handled via the official **Groq/OpenAI Tools API**, ensuring 100% stable execution without brittle regex or messy prompt instructions. 🧠📏
- **Sensory Notifications**: Real-time browser notifications and voice synthesis for reminders. 🔊🔔
- **Atomic Persistence**: SQLite integration with SQLAlchemy models for complete chat and task history. 📦

---

## 📁 System Architecture

```text
/
├── main.py              # Root Entrypoint (Delegates to app.main)
├── app/                 # The Hand-Crafted Backend Core
│   ├── routes/          # API Routers (chat, reminders, users)
│   ├── services/        # Business Logic (AIService, ReminderService)
│   ├── models/          # SQLAlchemy Models Package
│   ├── auth/            # JWT Handler & Security Logic
│   ├── celery_app.py    # Background Task Orchestrator
│   └── database.py      # Persistence Configuration
├── sidekick-frontend/   # React/Vite Application
└── static/              # Compiled Frontend Assets (Docker Deployment)
```

---

## 🛠 Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy, Uvicorn.
- **AI Engine**: Groq (Llama-3.3-70b-versatile) via formal Tool Calling.
- **Security**: Python-Jose (JWT), Passlib (BCrypt).
- **Background Tasks**: Celery, Redis.
- **Frontend**: React 18, Vite, TailwindCSS, Axios.

---

## 🚀 Deployment & Setup

### 1. Local Development (Standard)

**Backend Setup:**
1. Install dependencies: `pip install -r requirements.txt`
2. Configure `.env`: Include your `GROQ_API_KEY` and `REDIS_URL`.
3. Start Redis (required for Celery).
4. Run the launcher: `python main.py`
5. Start Celery Worker: `celery -A app.celery_app worker -l info`

**Frontend Setup:**
1. `cd sidekick-frontend`
2. `npm install`
3. `npm run dev`

### 2. Standardized Docker Deployment 🐳
The project is Docker-Ready using a multi-stage build that compiles the React frontend and serves it directly through FastAPI.

- **Build**: `docker-compose build`
- **Up**: `docker-compose up -d`

---

## 🔒 Security Note
This project uses **JWT Bearer Tokens**. Ensure `SECRET_KEY` in `app/config.py` is changed for any production environment. All API requests (except `/api/onboard`) must include the `Authorization: Bearer <token>` header.

---

## 🤝 Contributing
Sidekick AI Pro is designed with absolute package imports (`app.xxx`) to ensure stability. Please maintain this standard for any architectural contributions.

**Sidekick Pro (v7.5) — Engineered for stability, secured for privacy, and sassier than ever.** 🛡️🏢🚀✨
