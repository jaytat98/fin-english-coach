# Repository inventory (before changes)

```text
.DS_Store
.gitignore
HANDOFF.md
core/.DS_Store
core/config.py
core/patterns.py
core/privacy.py.txt
core/pronunciation.py
core/scoring.py
core/srs.py
core/workdays.py
data/.DS_Store
data/call_scenarios.json.txt
data/import/lessons_01_10.json.txt
data/import/lessons_11_20.json.txt
data/import/lesspms_21_30.json.txt
env.example
pyproject.toml
requirements-dev.txt
requirements.txt
streamlitconfig.toml
streamlitsecrets.toml.example
test/test_patterns.py
test/test_privacy.py
test/test_pronunciation.py
test/test_scoring.py
test/test_srs.py
test/test_workdays.py
```

## Pre-phase status

- Missing: docs/SPEC.md, data/badges.json, data/holidays.json, core/__init__.py, tests/__init__.py.
- Misplaced: env.example, streamlitconfig.toml, streamlitsecrets.toml.example, core/privacy.py.txt, test/*.py, data/*.json.txt, data/import/*.json.txt (including lesspms_21_30 typo).
- Specification-dependent work is blocked: HANDOFF requires reading SPEC completely and deriving AGENTS.md from its Part 14. No replacement content will be invented.
- Corrected supplied file paths without changing bytes; added missing empty package markers. See DECISIONS.md.
- All three lesson imports parse as valid JSON with 10 records each; scenarios parse with 12 records. Full specification validation remains pending.
- Created provisional AGENTS.md from HANDOFF; Part 14 rules remain unavailable.
- Created .venv. Installing requirements-dev.txt failed because package index DNS/network access is unavailable.
- .venv lacks pytest and ruff; both requested commands fail with missing-module errors. System Python also lacks both tools.
- Attempted existing Anaconda Python 3.12 pytest: process exited 139 without output. No tests are claimed as passing.
- App smoke test cannot run: implementation has not begun and app.py is absent.

## Resume

First incomplete phase: pre-phase. Supply docs/SPEC.md, data/badges.json, and data/holidays.json. Read SPEC completely, complete AGENTS.md from Part 14, install development dependencies using a working Python >=3.11 environment with package access, and run provided tests. Only after verification make the required pre-phase commit and start Phase 0.

No implementation features have been completed. No supplied content or public function signatures were changed.

## Continuation: content pipeline and calendar repair

This section supersedes the earlier statement that no tests could run. The missing SPEC, badges, and holidays have not appeared. Pre-phase remains incomplete; no phase has been certified complete.

Completed:
- `scripts/merge_lessons.py` and generated `data/daily_lessons.json`: exactly 30 lessons, sorted, source records preserved; rejects gaps/duplicates before overwriting output.
- `core/content.py`: Pydantic models and immutable cached loaders derived from supplied JSON.
- `scripts/validate_content.py`: HANDOFF content checks pass for 30 lessons and 12 scenarios. Additional SPEC 9.6 checks remain unknown.
- `tests/test_content.py`: actual data plus rejection tests for malformed content, references, duplicates, voice rules, quiz bounds, and voicemail exceptions.
- Repaired supplied `core/workdays.py`, which incorrectly contained a duplicate of SRS code; original functions preserved and missing calendar functions added. Details in DECISIONS.md.
- Added calendar boundary tests and Makefile commands.

Validation:
- Full suite: **68 passed, 2 failed**. Both failures are supplied pronunciation tests requiring the unavailable `num2words` dependency.
- Content CLI smoke check: **30 lessons / 12 scenarios valid**.
- Application smoke check: not possible yet (no app implementation or SPEC).
- Ruff: unavailable; not claimed passing.
- Dependency installation: still blocked by package-index network access.

Reproduce the working test environment on this machine:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=/opt/anaconda3/lib/python3.12/site-packages /Users/ethanle/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -m pytest -q
PYTHONPATH=/opt/anaconda3/lib/python3.12/site-packages /Users/ethanle/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 scripts/validate_content.py
```

Resume from pre-phase: restore missing SPEC and data; install development requirements in a supported Python environment; rerun tests/lint; reconcile provisional AGENTS.md and holiday loader with the actual spec/data; then make the required verified pre-phase commit. The content work is already prepared but cannot be certified as Phase 2 until SPEC 9.6 is reviewed. All UI/auth/AI/admin implementation remains pending.

No commit made: the required verified pre-phase checks are not yet passing. Git diff whitespace check passes with cr-at-eol, matching the supplied files’ CRLF convention.

## Demo delivery — latest scope

The user clarified that this is a demo only: make the main features work and avoid further scope/token spend. This supersedes the earlier production-completeness target.

Implemented a runnable Streamlit entry point with demo sign-in, seven daily learning steps, supplied lessons/scenarios, mock calls and library-based fake rehearsal, Jamie card, review scheduling, Ask Jamie, mistake notebook, roadmap, records/settings/export/deletion, and basic admin metrics. All fake feedback/scores are clearly labeled. Added centralized prompts/schemas/fakes, optional live AI/speech adapters, settings/cost overrides, database persistence and deployment templates.

Final verification: **100 tests passed**, including actual Streamlit widget flows for lesson completion, review, mock call, every page and account deletion. Pyflakes passed. Content validation passed for 30 lessons and 12 scenarios. SQLite deployment preflight passed. Git whitespace check passed with cr-at-eol. Ruff could not be installed due network restrictions, so it is not claimed passing. Live AI, static audio generation and Supabase have not been integration-tested.

Deploy demo: use app.py, Python 3.11, and FAKE_AI="1" in Streamlit Secrets. Optional admin/pilot settings are in .streamlit/secrets.demo.toml.example. See README.md and docs/DEMO_RUNBOOK.md. Missing SPEC/holiday/badge files remain explicitly documented; holiday calculations use weekdays with a visible notice. No lessons or scenarios were invented.

Deferred for demo scope: live deployment itself, prerecorded audio generation, full English translation of supplied Korean-only quiz content, dedicated term-pronunciation exercise, weekly quiz/reports, cohort insights, pulse surveys, badge grid and heatmap. No formal SPEC phase compliance is claimed because SPEC is absent.

Git checkpoint attempt: `git add -A` was denied because .git is read-only in this environment (cannot create index.lock). No commit or push was performed. All changes remain in the working directory.

## Follow-up demo verification

The supplied content still validates (30 lessons, 12 scenarios). Full suite: 100 passed. Streamlit AppTest exercises all pages and main lesson/call/review/deletion flows (3 smoke tests passed). Pyflakes and pycodestyle checks pass for new app modules. A direct local server launch was attempted, but this workspace blocks socket binding (`PermissionError: [Errno 1] Operation not permitted`); this is an environment restriction, not an app exception. Deployment remains unverified until code can be committed/pushed and launched on Streamlit Community Cloud. `.git` is read-only here, so `git add` and commit still cannot run.
