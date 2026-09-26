# Contributing to Astra AI

Thank you for your interest in contributing to **Astra AI**! We welcome bug reports, feature suggestions, and pull requests.

---

## Development Workflow

1. **Fork the repository** on GitHub.
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/<your-username>/InstagramSmart_chat_handler.git
   cd InstagramSmart_chat_handler
   ```
3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. **Create a feature branch**:
   ```bash
   git checkout -b feat/your-feature-name
   ```
5. **Run test suite** before committing:
   ```bash
   python -m unittest discover tests
   ```
6. **Commit with conventional commit messages**:
   - `feat: ...` for new features
   - `fix: ...` for bug fixes
   - `docs: ...` for documentation updates
   - `test: ...` for test additions
7. **Push and submit a Pull Request** to the `main` branch.

---

## Code Style & Standards

- Follow **PEP 8** style guidelines.
- Ensure all new public services and routes have corresponding unit tests under `tests/`.
- Do not commit `.env` or sensitive API keys.

---

## Reporting Issues

If you find a bug or have an idea for an enhancement, please open an issue in the [GitHub Issue Tracker](https://github.com/MrRanjan12/InstagramSmart_chat_handler/issues) with:
- A clear description of the behavior.
- Steps to reproduce.
- Relevant logs or stack traces.
