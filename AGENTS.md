# Project working instructions

This is a provisional transcription of HANDOFF.md only. Complete this file from docs/SPEC.md Part 14 when the missing specification is supplied.

- Read HANDOFF.md and docs/SPEC.md completely before implementation; HANDOFF overrides SPEC. Never overwrite SPEC.
- Preserve supplied files and public signatures. Extend only as needed; log genuine bug fixes in docs/DECISIONS.md with file, problem, change, and reason.
- Never invent lessons or scenarios or rewrite their wording. Derive content models from actual JSON.
- Follow phases in order; run ruff, pytest and smoke checks and update docs/PROGRESS.md before each phase commit. Never claim unverified work passed.
- Use core/workdays.py, core/patterns.py, core/privacy.py, core/scoring.py and core/config.py as the authoritative implementations described in HANDOFF.
- All AI calls must use centralized prompts and Pydantic schemas, with deterministic FAKE_AI support.
- Implement MUST features first, then SHOULD, then COULD. Record skipped features and changes to provided files.
- On interruption, record the first incomplete phase and exact blockers in docs/PROGRESS.md.
