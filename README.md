<div align="center">

# Astra AI

**An intelligent Instagram conversational assistant with persistent memory**

Built on FastAPI, Groq's Llama 3.3, PostgreSQL, and the Meta Messenger Platform

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Groq](https://img.shields.io/badge/Groq-Llama%203.3-F55036)](https://groq.com/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](#license)

[Overview](#overview) • [Architecture](#architecture) • [Getting Started](#getting-started) • [Configuration](#configuration) • [Roadmap](#roadmap)

</div>

---

## Overview

Astra AI is a production-ready conversational assistant for Instagram that combines large language model reasoning with persistent, structured memory. Unlike stateless chatbot implementations, Astra AI retains full conversation history per user, enabling genuinely context-aware, multi-turn dialogue over time.

**Core capabilities**

| Capability | Description |
|---|---|
| Conversational Memory | Every message and reply is persisted, allowing the assistant to recall prior context indefinitely |
| Context-Aware Responses | Full conversation history is passed to the LLM on each turn, not just the latest message |
| Instagram Integration | Native support for the Meta Messenger Platform webhook protocol |
| Automatic User Management | Users and conversations are provisioned automatically on first contact |
| Duplicate Message Protection | Guards against webhook retries and duplicate event delivery |
| Background Processing | Non-blocking message handling to keep webhook response times low |
| Production Deployment | Deployed and running on Render with a managed PostgreSQL instance |

---

## Architecture

### Project Structure

```
instagram_ai_assistant/
├── backend/
│   ├── models/          # SQLAlchemy ORM models
│   ├── services/         # Business logic and memory services
│   ├── ai_agent.py       # LLM agent and prompt orchestration
│   ├── config.py         # Environment and application configuration
│   ├── database.py       # Database session and engine setup
│   ├── instagram.py      # Instagram/Meta Messenger API client
│   ├── main.py            # FastAPI application entry point
│   └── webhook.py        # Webhook verification and event handling
├── logs/
├── db/
├── requirements.txt
├── README.md
└── .env
```

### Technology Stack

| Layer | Technology |
|---|---|
| Language | Python |
| API Framework | FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| LLM Provider | Groq API (Llama 3.3 70B Versatile) |
| Messaging Platform | Meta Messenger API (Instagram) |
| Deployment | Render |
| Version Control | Git / GitHub |

### Data Model

```
User                        Conversation                 Message
├── id                      ├── id                       ├── id
├── instagram_id            ├── user_id (FK)              ├── conversation_id (FK)
├── current_mode            └── created_at                ├── role
└── created_at                                             ├── content
                                                            └── created_at
```

**Relationships:** One `User` has many `Conversations`; one `Conversation` has many `Messages`, each tagged with a `role` (`user` or `assistant`) to preserve turn order for the LLM context window.

---

## Getting Started

### Prerequisites

- Python 3.11 or later
- A PostgreSQL database instance
- A Groq API key
- A configured Meta Messenger / Instagram app with webhook access

### Installation

```bash
git clone https://github.com/MrRanjan12/InstagramSmart_chat_handler.git
cd <local_file_name>
```

Create and activate a virtual environment:

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
VERIFY_TOKEN=your_webhook_verify_token
PAGE_ACCESS_TOKEN=your_page_access_token
DATABASE_URL=postgresql://username:password@host/database
```

### Running Locally

```bash
uvicorn backend.main:app --reload
```

---

## Example Interaction

```
User:    Hi
Astra:   Hello! 👋

User:    My name is Ranjan.
Astra:   Nice to meet you, Ranjan!

User:    What's my name?
Astra:   Your name is Ranjan. 😊
```

---

## Deployment

Astra AI currently runs in production on the following stack:

- **Hosting:** Render
- **Database:** Managed PostgreSQL using Neon
- **Messaging:** Meta Webhooks
- **Inference:** Groq API

---

## Roadmap

### Shipped — v2.0

- [x] PostgreSQL integration
- [x] Persistent conversational memory
- [x] Context-aware AI responses
- [x] Production deployment

### Planned

- [ ] Human handoff support
- [ ] Assistant switching (multi-persona)
- [ ] Autonomous mode
- [ ] Conversation analytics
- [ ] Admin dashboard
- [ ] Long-term memory summarization
- [ ] Multi-agent orchestration

### Vision

Astra AI is being built as a channel-agnostic conversational platform, extending beyond Instagram to WhatsApp, Facebook Messenger, Telegram, web chat, and voice — all backed by a shared memory and conversation engine.

---

## Author

**Ranjan Prajapati**
Software Engineer · AI Developer · Full Stack Developer

[GitHub](https://github.com/MrRanjan12)

---

## License

This project is available under the MIT License.

If you find this project useful, consider giving it a star on GitHub — it helps support continued development.