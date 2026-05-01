# Architecture

## Design goals

- Keep the first release local-first and easy to reason about
- Put policy checks between the assistant and every tool call
- Treat anything from the web, documents, and messages as untrusted input
- Make risky actions replayable through a durable audit log
- Grow from a safe MVP without rewriting core service boundaries

## Service map

### Interface service

The current repo includes a static dashboard prototype and a FastAPI-shaped backend entrypoint. In a full product, this becomes the desktop shell plus voice, notifications, and settings.

### Orchestrator

The orchestrator accepts user input, classifies intent, chooses a tool, asks the policy engine for approval requirements, and either executes or stages the action.

### Policy engine

The policy engine maps every action to a permission level:

- `safe_read`: execute automatically
- `low_risk`: require user confirmation
- `sensitive`: require user confirmation
- `high_risk`: require strong confirmation, and block in safe mode

### Memory service

Conversation memory is stored in SQLite with an explicit enable/disable flag. The schema is designed so short-term and long-term memory can be separated later.

### Tool execution layer

Each tool is wrapped in a typed definition that declares:

- category
- permission level
- description
- execution handler

The first tool set is intentionally small and safe:

- system snapshot
- web search handoff
- open website proposal
- create note
- draft email

### Logging and audit

Every proposed, executed, blocked, or failed action is appended to a JSONL audit log. This keeps the approval model observable from day one.

## Trust boundaries

1. User input enters the orchestrator.
2. The orchestrator produces a structured proposed action.
3. The policy engine evaluates the action before tool execution.
4. The audit logger records the policy decision and result.
5. Only then does the tool layer run.

This prevents raw assistant text, scraped web content, or document content from directly triggering tools.

## Runtime data

- `backend/data/audit/actions.jsonl`: immutable-ish append-only action history
- `backend/data/memory/conversations.sqlite3`: local memory store
- `notes/`: approved write target for note creation

## Upgrade path

- Replace keyword routing with an LLM planner that emits the same action contract
- Add a desktop shell for native automation and voice I/O
- Add connector processes for browser automation, messaging, and system control
- Introduce secret storage and encrypted memory at phase 4
