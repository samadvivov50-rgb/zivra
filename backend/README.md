# Backend

The backend is organized around durable service boundaries rather than framework glue.

## Key modules

- `app/core/config.py`: runtime settings, browser voice preferences, and approved directories
- `app/models.py`: shared enums and dataclasses for actions and results
- `app/services/policy.py`: approval logic and safe-mode enforcement
- `app/services/memory.py`: SQLite-backed conversation memory
- `app/services/audit.py`: append-only action logging
- `app/services/content.py`: local YouTube title, SEO copy, and creator package generation
- `app/services/browser_launch.py`: isolated browser launch helpers with private-window preference and safe fallback behavior
- `app/services/emails.py`: local email outbox storage plus SMTP delivery
- `app/services/messages.py`: WhatsApp draft storage, Meta Cloud API send/inbox persistence, webhook handling, and browser-handoff fallback delivery
- `app/services/prompt_injection.py`: shared prompt-injection detection and sanitization for untrusted sources
- `app/services/research.py`: compact research briefs built from live search and sanitized webpage summaries
- `app/services/secrets.py`: encrypted local secret storage and runtime secret application
- `app/services/sync.py`: mobile companion snapshots and explicit JSON export for trusted local sync flows
- `app/services/vision.py`: screenshot, camera-frame, and image inspection with local metadata fallback plus optional multimodal summaries
- `app/services/workflows.py`: scheduled workflow storage, queue dispatch, bounded supervisor cycles, and workflow recovery state
- `app/services/planning.py`: rule-based and optional LLM-backed planning with fallback validation
- `app/services/orchestrator.py`: planner integration, policy checks, and execution flow
- `app/tools/`: tool definitions, implementations, and registry
- `app/api/routes/`: FastAPI route layer

## Quick start

Once Python 3.12+ is available, use this flow:

1. Create a virtual environment or use `uv`.
2. Install dependencies from `pyproject.toml`.
3. Optionally set `ZIVRA_SMTP_HOST`, `ZIVRA_SMTP_PORT`, `ZIVRA_EMAIL_FROM`, and any needed SMTP credentials if you want local outbox drafts to be sendable.
4. Optionally set `ZIVRA_VISION_MODEL` plus an OpenAI-compatible API key if you want screenshot uploads and camera captures to receive multimodal scene summaries instead of metadata-only fallback.
5. Website opens, workspace URL opens, and WhatsApp sends will use Meta Cloud API when `ZIVRA_WHATSAPP_PHONE_NUMBER_ID` plus a WhatsApp access token are configured; otherwise they prefer an isolated private browser handoff and fall back to the default browser when isolation is unavailable.
6. For WhatsApp Cloud API inbox support, point your Meta webhook to `/messages/whatsapp/webhook`, set `ZIVRA_WHATSAPP_VERIFY_TOKEN` or save a verify token in Settings, and optionally add a WhatsApp app secret for webhook signature validation.
7. From the repo root, use `.\start-zivra.cmd` for a normal run, `.\stop-zivra.cmd` to stop the tracked server, and `.\check-zivra.cmd` to run tests and syntax checks.
8. For direct script control, `.\scripts\start-zivra.ps1 -Reload` runs the backend in development reload mode, `.\scripts\start-zivra.ps1 -BindHost 0.0.0.0` exposes it to your LAN, `.\scripts\start-zivra.ps1 -StateName demo` tracks a separate launcher slot, and `.\scripts\start-zivra.ps1 -DataDir .\backend\data\test-runs\demo` points the run at isolated state.
9. `.\scripts\check-zivra.ps1 -SmokeLaunch` verifies the launcher path on an isolated port and data directory instead of touching the default tracked server.
10. From the repo root, `npm install` plus `npm run test:smoke` runs the Playwright desktop/mobile smoke suite against its own isolated backend data at `backend\data\test-runs\playwright-smoke`. The suite prefers a locally installed Chrome or Edge when Playwright-managed browser downloads are unavailable.
11. The desktop control room is at `/ui/`, the mobile companion PWA is at `/mobile` or `/ui/mobile.html`, and `/sync/access` exposes same-network companion URLs plus session-aware handoff links for desktop sharing, including a preferred same-network candidate when one can be inferred. The companion feed also preserves grouped pending actions so mobile can review linked approval batches coherently.
