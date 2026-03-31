# 🤖 Sidekick: Multi-Process AI Agent

An event-driven, asynchronous AI assistant designed to handle real-time chat and background task scheduling. By decoupling the LLM orchestration (**FastAPI**) from the task execution (**Celery/Redis**), Sidekick ensures a zero-latency user experience even when scheduling complex future events.

---

## 🏗️ System Architecture

The application is built using a modern 3-tier distributed architecture to ensure scalability and separation of concerns:

* **Frontend Layer:** React 18 (Vite) + Tailwind CSS + Framer Motion (State-aware animations).
* **API Gateway:** FastAPI (Python 3.12) handling LLM orchestration and tool calling logic.
* **Async Task Queue:** Celery + Redis for out-of-band execution (Scheduled Reminders).
* **Persistence:** SQLAlchemy + SQLite for message history and relational data storage.

---

## 🚀 Key Features

* **Non-Blocking Task Injection:** Reminders are pushed to a Redis queue, allowing the API to return responses to the user instantly while the worker handles the countdown.
* **Dynamic Identity:** The bot's name and personality are injected via Pydantic settings, allowing for hot-swappable AI personas without changing frontend code.
* **Rich Media Rendering:** Full Markdown support for code snippets, lists, and bold text within the chat interface.
* **Short-Term Persistence:** Full message history is stored and retrieved per session, providing the LLM with consistent context.

---

## 🛠️ Installation & Setup

### 1. Backend Environment
```bash
# Clone and enter directory
cd Sidekick

# Initialize virtual environment
python -m venv sidevenv
source sidevenv/bin/activate

# Install dependencies
pip install -r requirements.txt

Frontend Environment:
cd sidekick-frontend
npm install

Environment Variables:
Create a .env file in the root directory:

GOOGLE_API_KEY=your_gemini_api_key
BOT_NAME=Hafsa
DATABASE_URL=sqlite:///./sidekick.db
REDIS_URL=redis://localhost:6379/0

🏃 Running the Application

To run the full agentic system, initialize the following services in separate terminals:
Service	Command	Port
Message Broker	sudo service redis-server start	6379
Backend API	uvicorn main:app --reload	8000
Celery Worker	celery -A celery_app worker --loglevel=info	-
React UI	cd sidekick-frontend && npm run dev	5173
