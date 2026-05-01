# Contributing

Thanks for contributing to Zivra.

## Workflow

- Create a feature branch from `main`.
- Keep changes focused and small.
- Write clear commit messages that explain intent.
- Open a pull request for review instead of pushing directly to `main`.

## Local setup

- Start app: `.\start-zivra.cmd`
- Run checks: `.\check-zivra.cmd -SmokeLaunch`
- Run smoke tests: `npm run test:smoke`

## Code and tests

- Add or update tests for behavior changes.
- Keep docs updated when commands, flows, or defaults change.
- Avoid committing local runtime state (`backend/data/`) or local agent metadata (`.codex/`).

## Pull request checklist

- [ ] Scope is focused and easy to review
- [ ] Tests pass locally
- [ ] Docs are updated if needed
- [ ] No secrets or machine-specific files included
