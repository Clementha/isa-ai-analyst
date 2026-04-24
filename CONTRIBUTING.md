# 🤝 Contributing to ISA AI Analyst

Thank you for taking the time to contribute! This document explains everything you need to get started — from setting up a local development environment to submitting a Pull Request.

---

## 📋 Table of Contents

- [Code of Conduct](#-code-of-conduct)
- [Ways to Contribute](#-ways-to-contribute)
- [Getting Started (Local Dev Setup)](#-getting-started-local-dev-setup)
- [Branching Convention](#-branching-convention)
- [Making Changes](#-making-changes)
- [Pull Request Process](#-pull-request-process)
- [Coding Conventions](#-coding-conventions)
- [Reporting Bugs](#-reporting-bugs)
- [Suggesting Features](#-suggesting-features)

---

## 🧭 Code of Conduct

Be respectful, constructive, and collaborative. This is a welcoming project — contributions of all experience levels are appreciated. Disrespectful or dismissive behaviour will not be tolerated.

---

## 💡 Ways to Contribute

You don't have to write code to contribute. Here are some valuable ways to help:

- 🐛 **Report a bug** — open a [GitHub Issue](https://github.com/ClementHa/isa-ai-analyst/issues)
- 💬 **Suggest a feature** — start a [GitHub Discussion](https://github.com/ClementHa/isa-ai-analyst/discussions)
- 📝 **Improve documentation** — fix typos, clarify steps, add examples
- 🧪 **Write tests** — help expand test coverage for `math_engine.py` or the OpenClaw integration
- 🌍 **Translate** — help make the README or setup guide accessible in other languages
- ⭐ **Star the repo** — it helps others discover the project

---

## 🛠️ Getting Started (Local Dev Setup)

### Prerequisites

- Python 3.10+
- Docker Desktop
- Git

### Fork and Clone

1. Click **Fork** at the top-right of the GitHub page to create your own copy
2. Clone your fork locally:

```bash
git clone https://github.com/YOUR_USERNAME/isa-ai-analyst.git
cd isa-ai-analyst
```

3. Add the upstream remote so you can pull future changes from the main repo:

```bash
git remote add upstream https://github.com/ClementHa/isa-ai-analyst.git
```

### Set Up Your Environment

Copy the example environment file and fill in your own API keys for testing:

```bash
cp .env.example .env
# Edit .env with your own keys
```

To run the math engine locally for development:

```bash
pip install requests
python math_engine.py
```

To run the full stack via Docker:

```bash
docker compose up -d --build
```

---

## 🌿 Branching Convention

Always branch off `main`. Use the following naming format:

| Type | Branch name example |
|---|---|
| Bug fix | `fix/telegram-pairing-timeout` |
| New feature | `feat/backtesting-engine` |
| Documentation | `docs/update-windows-setup` |
| Refactor | `refactor/math-engine-cleanup` |

```bash
git checkout main
git pull upstream main
git checkout -b feat/your-feature-name
```

---

## ✏️ Making Changes

- Keep each PR focused on **one concern** — avoid bundling unrelated changes together
- Test your changes locally before submitting
- If your change affects the report output format, update the **Reading the Report** section in `README.md` accordingly
- If your change adds a new `.env` variable, add it to both `.env.example` and the **Environment Variable Reference** table in `README.md`

---

## 📬 Pull Request Process

1. Push your branch to your fork:

```bash
git push origin feat/your-feature-name
```

2. Open a Pull Request against the `main` branch of the upstream repo
3. Fill in the PR template — describe **what** you changed and **why**
4. Link any related Issues (e.g. `Closes #42`)
5. A maintainer will review your PR — please be patient and responsive to feedback
6. Once approved, your PR will be squash-merged into `main`

> ⚠️ PRs that modify `math_engine.py` or the 3-gate logic require particular care — please explain your reasoning clearly and include test output showing the change in behaviour.

---

## 🧹 Coding Conventions

- **Python:** Follow [PEP 8](https://peps.python.org/pep-0008/). Use descriptive variable names — avoid single-letter names outside of loop counters.
- **Comments:** Write comments that explain *why*, not *what*. The code should be readable enough that line-by-line narration isn't needed.
- **Error handling:** All external API calls must be wrapped in `try/except` with a meaningful fallback or log message — never let an API failure crash the entire report run.
- **No secrets in code:** All API keys and tokens must be read from the `.env` file via `get_secret()` — never hardcoded.
- **Emoji in output:** The report output style (👍 👎 🟢 🔴 etc.) is intentional and part of the user experience — please preserve it in any changes to report generation.

---

## 🐛 Reporting Bugs

Open a [GitHub Issue](https://github.com/ClementHa/isa-ai-analyst/issues) and include:

- A clear description of the problem
- Steps to reproduce it
- Relevant log output (from `docker compose logs -f` or setup script option 8)
- Your OS and Docker Desktop version
- Whether you're using a cloud LLM (OpenRouter) or a local LLM (Ollama)

Please **redact all API keys** before pasting any logs or `.env` contents.

---

## 🚀 Suggesting Features

Open a [GitHub Discussion](https://github.com/ClementHa/isa-ai-analyst/discussions) rather than an Issue for feature ideas — it's a better format for open-ended conversation. Include:

- What problem the feature solves
- Who would benefit from it
- Any rough idea of how it might work

The most requested features will be prioritised in the [Roadmap](README.md#-roadmap).
