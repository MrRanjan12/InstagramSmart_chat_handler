# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.1.0] - 2026-09-26

### Added
- **Intent Scoring Engine**: Real-time scoring ($0–100$) based on user inquiry complexity, sentiment markers, and urgent keywords.
- **Bilingual Human Escalation Detector**: Keyword and phrase boundary detection supporting both English and Hinglish phrases (e.g., *"asli ranjan"*, *"bot ho kya"*, *"talk to a human"*).
- **Stateful Hybrid Routing**: Mode tracking via PostgreSQL (`users.current_node`) to gracefully switch between `ASTRA` (AI) and `RANJAN` (Human takeover).
- **Automatic Inactivity Switching**: Time-to-live (TTL) silence monitor that automatically reverts conversations from `RANJAN` back to `ASTRA` after configurable hours (default: 12h).
- **Escalation Management APIs**:
  - `GET /api/escalation/status/{instagram_id}`
  - `POST /api/escalation/switch/{instagram_id}`
  - `POST /api/escalation/reset/{instagram_id}`
  - `POST /api/escalation/test-intent`
- **Automated Test Suite**: Added `tests/test_escalation.py` with 100% passing tests for keyword triggers, scoring boundaries, and auto-reset time arithmetic.
- **Containerization**: Added production `Dockerfile` and `docker-compose.yml` with PostgreSQL 16 container.
- **Continuous Integration**: Added `.github/workflows/ci.yml` for automated GitHub Actions test verification on every commit.

### Changed
- Webhook asynchronous processing pipeline (`webhook.py`) now intercepts messages and verifies escalation routing before delegating to the Groq/LLM service.
- Upgraded project metadata and packaging to `pyproject.toml` (PEP 621).

---

## [2.0.0] - 2026-09-20

### Added
- **PostgreSQL Persistence**: Persistent message and conversation tracking via SQLAlchemy ORM.
- **Context-Aware Conversational Memory**: Sliding window context memory for multi-turn dialogue.
- **Llama 3.3 Integration**: High-speed, high-intelligence LLM responses powered by Groq API.
- **Webhook Deduplication**: Message ID cache protection against Meta retry spam.
- **Render Production Deployment**: Automated CI/CD deployments connected to GitHub.

---

## [1.0.0] - 2026-08-15

### Added
- Initial release of Instagram assistant webhook receiver.
- Meta Messenger Platform token verification and basic echo handling.
