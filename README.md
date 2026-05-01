# Zivra Assistant

Zivra is a local-first AI assistant foundation for desktop productivity. This starter repository turns your blueprint into a concrete MVP-oriented codebase with a Python orchestration backend, a permission-aware policy layer, conversation memory, audit logging, and a lightweight dashboard prototype.

## What is in this starter

- A local-first backend architecture for orchestration, memory, policy checks, tools, audit logs, and encrypted local secrets
- A policy model that clearly separates safe reads from approval-gated side effects
- A planner layer with rule-based routing and optional OpenAI-compatible planning, plus validated multi-step action handling
- A broad local toolset spanning system info, safe web/research flows, notes/docs/files, reminders, clipboard, vision, messaging, and email
- A dashboard experience for chat, approvals, notes/docs inspection, audit timelines, workflows, secrets/preferences management, and companion handoff
- Companion/mobile sync and handoff support for same-network usage
- Architecture and roadmap documentation aligned with the current codebase

## Repository layout

- `backend/`: FastAPI-oriented backend scaffold and pure-Python core services
- `dashboard/`: dependency-light dashboard prototype for the MVP experience
- `docs/`: approved read-only product documents used by the document search and reader
- `notes/`: approved local note workspace used by the note tool
- `scripts/`: Windows-friendly start, stop, and verification scripts for local runs and demos

## Quick start

For the easiest Windows flow from the repo root:

- Start the app: `.\start-zivra.cmd`
- Stop the tracked local server: `.\stop-zivra.cmd`
- Run verification checks: `.\check-zivra.cmd`

Helpful options:

- Dev reload mode: `powershell -File .\scripts\start-zivra.ps1 -Reload`
- Bind to your LAN for another device: `powershell -File .\scripts\start-zivra.ps1 -BindHost 0.0.0.0`
- Open the mobile companion too: `powershell -File .\scripts\start-zivra.ps1 -OpenMobile`
- Include a launcher smoke test in verification: `powershell -File .\scripts\check-zivra.ps1 -SmokeLaunch`
- Track a separate launcher instance without touching the default server state: `powershell -File .\scripts\start-zivra.ps1 -StateName demo`
- Point a run at an isolated backend data directory: `powershell -File .\scripts\start-zivra.ps1 -DataDir .\backend\data\test-runs\demo`

## Playwright smoke suite

For the new release-grade UI smoke coverage from the repo root:

- Install frontend test dependencies: `npm install`
- Run the desktop/mobile smoke suite: `npm run test:smoke`
- Run it headed while debugging: `npm run test:smoke:headed`
- Install Playwright-managed Chromium if you want it: `npm run install:browsers`

The smoke setup starts its own isolated Zivra instance on port `8011`, uses its own launcher state, and writes into `backend\data\test-runs\playwright-smoke`, so it does not reuse your normal reminders, outbox, memory, or tracked local server. When Playwright browsers are unavailable, the suite automatically falls back to a locally installed Chrome or Edge executable if one is present.

## Features

Zivra currently includes:

- Local-first FastAPI backend with a lightweight dashboard served from `/ui`
- Session-based assistant chat (`session_id`) with SQLite-backed history
- Planner-backed orchestration with guarded multi-step execution
- Policy-gated actions where safe reads can auto-run and side effects require confirmation
- Broad built-in tools: system info, live web search, safe webpage summarization, docs/files/notes, reminders, email drafts/send, WhatsApp drafts/cloud send, clipboard, and vision/image analysis
- Prompt-injection-aware sanitization for untrusted web and document inputs
- Local preferences and encrypted secrets storage, including optional OpenAI-compatible planner settings and SMTP settings
- Audit-first transparency with timeline-style action history and approval review in the dashboard
- Mobile companion handoff and sync snapshot support for same-network usage
- Automated quality checks with backend tests plus Playwright desktop/mobile smoke coverage

## Current limitations

This MVP still has important limits:

- No user registration/login/JWT auth; the app is local-first and session-based, not account-based
- No multi-tenant user isolation model for chats, documents, memory, or tool state
- SQLite-backed local storage only; no production DB/migrations stack yet
- No built-in RAG/vector database pipeline (for example, ChromaDB-backed embeddings and semantic retrieval)
- No full production hardening by default (managed secrets, HTTPS edge config, deployment ops, centralized monitoring)
- No streaming token-by-token chat responses in the current dashboard flow
- Tool orchestration is practical but still intentionally constrained compared with large-scale autonomous agent frameworks
- Document workflows are strong for local search/read/summarize/inspect flows, but can still improve on ranking quality and citation UX
- No default Docker deployment path in this starter; local script-first development is the primary path
- Background processes are local-machine dependent and may need manual restart after reboot/session end

## Practical Status

Zivra is a strong local MVP for testing policy-aware assistant workflows with transparent tools, local data control, and integrated dashboard/mobile handoff.

It is not production-ready yet. Treat this repository as a local foundation that still needs authentication/authorization, deployment hardening, migration strategy, and broader operational safeguards before serious multi-user deployment.

## Suggested next steps

### Local Dev

1. Install Python 3.12+ and sync backend dependencies with `uv`.
2. Configure optional planner/vision variables: `ZIVRA_PLANNER_MODE`, `ZIVRA_LLM_MODEL`, `ZIVRA_VISION_MODEL`, and `OPENAI_API_KEY` or `ZIVRA_LLM_API_KEY`.
3. Configure optional SMTP variables (`ZIVRA_SMTP_HOST`, `ZIVRA_SMTP_PORT`, `ZIVRA_EMAIL_FROM`, and credentials) if you want local outbox delivery.
4. Run `.\start-zivra.cmd` for normal startup, or `.\scripts\start-zivra.ps1 -Reload` while developing.

### Quality Checks

1. Run `.\check-zivra.cmd -SmokeLaunch` for backend and launcher verification.
2. Run `npm run test:smoke` for desktop/mobile Playwright smoke coverage before release-oriented changes.

### Roadmap

1. Add a real desktop shell (Electron or Tauri) for richer native capabilities.
2. Move from the current dashboard prototype to a React-based surface once the UI direction is finalized.
3. Expand browser automation depth and strengthen approval UX on top of the existing policy engine.

## Current assumptions

- Local-first is the default operating mode
- Safe reads may run immediately
- Low-risk and sensitive actions require confirmation
- High-risk actions require strong confirmation and are blocked in safe mode
- Approved write and read roots are policy-controlled by runtime settings
