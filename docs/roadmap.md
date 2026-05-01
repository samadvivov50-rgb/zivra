# Roadmap

## Phase 1: Safe local MVP

- Text-first assistant loop
- Intent routing and task classification
- Policy-gated tool execution
- System info
- Web search handoff
- Website launch confirmation
- Notes
- Draft email
- Audit logging
- Memory toggle

## Phase 2: Daily productivity

- Real web search integration
- File search and organization
- Workspace launcher
- Clipboard tools
- Browser read automation
- Settings and personalization

## Phase 3: Communication workflows

- Email send with approval
- Messaging connectors with approval
- Research summaries
- YouTube and SEO helpers
- CSV exports and lightweight analysis

## Phase 4: Security hardening

- Encrypted secrets
- Memory controls and deletion UI
- Restricted folder allowlists
- Browser isolation
- Prompt-injection sanitation
- Audit dashboard
- Kill switch and safe mode

## Phase 5: Multimodal expansion

- Voice input
- TTS
- Camera and screenshot understanding
- Mobile companion
- Sync

## Phase 6: Controlled agent mode

- Scheduled workflows
- Task queues
- Background supervisors
- Rollback and recovery

## Engineering order

1. Finish the local orchestrator contract and approval UX.
2. Add a real desktop runtime for native actions.
3. Introduce LLM planning behind the existing action schema.
4. Expand the tool surface only after policy and logging stay reliable.
