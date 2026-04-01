---
title: SideKickBot
emoji: 💃
colorFrom: pink
colorTo: pink
sdk: docker
pinned: false
---

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
