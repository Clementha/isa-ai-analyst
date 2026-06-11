# Security Policy

ISA AI Analyst runs entirely on your own machine in a Docker container, with
read-only broker access. It cannot place trades. This document explains how to
report issues, what's protected, and what stays your responsibility.

## Reporting a Vulnerability

Please report security issues **privately** — do not open a public issue.

Use GitHub → **Security** tab → **Report a vulnerability** (private advisory).

I'm a solo maintainer, so responses are best-effort — typically within a few days.
Please include steps to reproduce and the affected version/commit.

## Supported Versions

Only the **latest release** receives security updates. Always run the most recent
version (see Releases). Older tags are not patched.

| Version        | Supported |
|----------------|-----------|
| Latest release | ✅        |
| Older          | ❌        |

## Security Model (what the project does)

- **Read-only broker access** — Trading 212 is used with read-only API scopes; the
  bot never has trade-execution or withdrawal permissions.
- **Containerised & sandboxed** — runs in Docker with **no Docker socket mounted**,
  **not privileged**, an isolated bridge network, and **no published ports**.
- **Input handling** — external inputs are URL-encoded for API calls, stock-name
  arguments are validated, and report content is HTML-escaped before delivery.
- **Bounded cost** — OpenRouter/EODHD usage is capped by your own provider limits.
- **Dependencies kept current** — the OpenClaw framework is pinned and bumped to
  pull security fixes (see Releases for the changelog).

## Your Responsibilities (self-hosted)

- Keep your `.env` secret — it holds all API keys (it's gitignored; never commit it).
- Trading 212 key: enable **only** Account data, Metadata, Portfolio. Leave
  **Orders/Pies OFF**.
- OpenRouter: disable auto top-up and set a spending limit.
- **Keep OpenClaw updated** — bump the pinned version periodically (check the
  OpenClaw CVE tracker). A pinned dependency does not auto-patch.
- Don't expose the gateway — do not add published ports or host networking.

## Known Limitations & Accepted Risks

- A Docker container is not a full VM (see the README footnote on isolation).
- Stock-name validation is defense-in-depth, not a sole barrier; safety also relies
  on argv-based command execution.
- Prompt-injection via third-party news content is mitigated (structured data,
  constrained prompts) but not eliminated.
- The local gateway auth token is stored in plaintext on your machine — acceptable
  because nothing is network-exposed by default.

## Disclaimer

This is educational software, not financial advice. See the README disclaimer.
