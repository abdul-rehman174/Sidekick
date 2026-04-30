---
title: Sidekick
emoji: 💖
colorFrom: pink
colorTo: purple
sdk: docker
app_port: 7860
pinned: true
license: mit
---

# Sidekick

A persona-cloning chat app. Each user logs in with a username + PIN; their chats stay private per account. The bot learns how to sound like a specific person when you paste their real messages as a **behavior profile**, and you can layer extra rules on top via a **system instruction**.

## How the persona works

The system prompt sent to the model is assembled from three user-controlled pieces:

1. **`persona_name`** — who the bot is pretending to be.
2. **`behavior_profile`** — pasted chat samples from that person. The model mirrors their vocabulary, slang, tone, punctuation, and language mix.
3. **`system_instruction`** — additional instructions you want applied on top ("respond in Roman Urdu", "stay playful", etc).

Open **Persona settings** in the sidebar to edit any of these at any time.

## Stack

- **Backend:** FastAPI, async SQLAlchemy, aiosqlite (default) or Postgres (asyncpg), Groq `llama-3.3-70b-versatile` via `AsyncGroq`
- **Auth:** JWT bearer tokens, bcrypt-hashed PINs
- **Frontend:** React 19 + Vite + Tailwind

## Setup

1. `cp .env.example .env` and fill in `GROQ_API_KEY` and `SECRET_KEY` (generate with `python -c 'import secrets; print(secrets.token_urlsafe(32))'`).
2. `pip install -r requirements.txt`
3. `python main.py` (backend on `:7860`)
4. `cd sidekick-frontend && npm install && npm run dev` (frontend on `:5173`)

## Docker

```
docker compose up --build
```

Frontend is built into `static/` and served from the FastAPI app on port 7860.

## API

| Method | Path | Body | Purpose |
|---|---|---|---|
| `POST` | `/api/onboard` | `{username, pin, persona_name?}` | Register or log in. Returns JWT. |
| `GET`  | `/api/persona` | — | Current persona settings. |
| `PUT`  | `/api/persona` | `{persona_name?, behavior_profile?, system_instruction?}` | Update any subset. |
| `POST` | `/api/chat` | `{user_message}` | Send a message, get `{reply, new_reminder?}`. |
| `GET`  | `/api/chat/history` | — | Last 50 messages. |
| `POST` | `/api/clear-all` | — | Wipe chats + reminders for the account. |
| `GET`  | `/api/reminders?status=pending\|completed` | — | List reminders. |
| `DELETE` | `/api/reminders/{id}` | — | Delete. |
| `POST` | `/api/reminders/{id}/complete` | — | Mark complete. |

All `/api` endpoints except `/api/onboard` require `Authorization: Bearer <token>`.

## Tests

```
pytest tests/
```
