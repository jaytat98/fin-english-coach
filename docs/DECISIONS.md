# Decisions

## Pre-phase: restore supplied file paths

The repository arrived with missing dot prefixes, .txt suffixes, tests in test/, and a lesspms filename typo. Renamed the following files without changing their bytes so imports, pytest discovery, and content loading can use the HANDOFF paths:

- `env.example` → `.env.example`
- `streamlitconfig.toml` → `.streamlit/config.toml`
- `streamlitsecrets.toml.example` → `.streamlit/secrets.toml.example`
- `core/privacy.py.txt` → `core/privacy.py`
- `test` → `tests`
- `data/call_scenarios.json.txt` → `data/call_scenarios.json`
- `data/import/lessons_01_10.json.txt` → `data/import/lessons_01_10.json`
- `data/import/lessons_11_20.json.txt` → `data/import/lessons_11_20.json`
- `data/import/lesspms_21_30.json.txt` → `data/import/lessons_21_30.json`

Added empty core/__init__.py and tests/__init__.py package markers listed as provided but absent. No supplied function signatures or learning content were changed. Missing SPEC, badges and holidays were not fabricated.

## Continuation with missing specification

The user requested continued work after the missing files were reported. Implemented only the content pipeline explicitly described in HANDOFF and the calendar bug exposed by the provided tests. This is preparatory work; no SPEC phase is marked complete, and SPEC Parts 9.6 and 14 still need review. No replacement specification, badge content, holiday dates, lessons, or scenarios were authored.

## Genuine supplied-module bug: core/workdays.py

Problem: the supplied file is byte-for-byte a duplicate of core/srs.py and exports none of the functions imported by tests/test_workdays.py. Pytest failed during collection with missing current_streak. Added the workday, lesson scheduling, and streak functions described in HANDOFF and exercised by the supplied tests. Preserved all existing functions/signatures, including the misplaced SRS functions, to avoid breaking the supplied API. Streak inputs are on-time completion dates; weekends/holidays cannot count toward a streak. Today's unfinished working day has a grace period, as required by the supplied tests.

The holiday loader currently expects a list of objects with ISO `date` and `country` fields and filters selected countries. This format is provisional until the missing holidays file and SPEC are restored; missing files raise rather than silently assuming no holidays.

## Content model and import decisions

- Derive Pydantic models from all supplied lesson/scenario records; reject unknown fields, invalid keys/voices, invalid quiz answers, and inconsistent weeks.
- Keep cached models deeply immutable by using frozen models and tuples.
- The field `register` uses the Python attribute `register_` with a JSON alias because BaseModel inherits an ABC `register` attribute. Serialize with `by_alias=True` to retain the source JSON shape.
- Detect duplicate phrases by phrase text, terms by term name across every service line, and tips by their incorrect example. Normalize case/whitespace; pattern keys are intentionally reusable.
- Merge validates exactly days 1–30 before replacing the output and preserves every source record value. Validator reads fresh files instead of cached data.
- Full SPEC validation is pending; the CLI explicitly reports HANDOFF checks only.

## Test environment

The default Python is 3.9, below the project's >=3.11 requirement. The installed Anaconda Python 3.12 crashes in readline during pytest startup. A cached Codex Python 3.12 runtime works with the installed Anaconda packages on PYTHONPATH and pytest plugin autoload disabled. It runs the suite; num2words is absent, leaving two supplied pronunciation tests failing. This is a missing dependency, not evidence that pronunciation.py should be rewritten. Ruff is also unavailable. Network restrictions prevented installing requirements-dev.txt.

## Deployable demo scope (user clarification)

The user explicitly requested working until Streamlit deployment was possible, then clarified this is only a demo and main features are enough. Implemented a self-contained FAKE_AI experience without inventing missing specification/content. Live integration and optional features are deferred.

Additional changes to supplied files:
- core/config.py: appended settings for strong-tier model/prices, shadowing STT, program-start configuration status, and app sharing URL. Extended Prices and estimate_cost's implementation to support minute-based TTS while retaining its public signature and legacy character-based defaults. Strong defaults verified against https://developers.openai.com/api/docs/models/gpt-4o; deprecated model names remain as required by HANDOFF and can be overridden.
- core/pronunciation.py: the optional-dependency fallback returned raw digit tokens, failing two supplied tests without num2words. Added a bounded English-number fallback in core/number_words.py, retaining existing signatures and using num2words normally when available. All provided tests now pass.
- requirements.txt: raised Streamlit minimum from 1.20 to 1.40 because st.audio_input became generally available in 1.40 (https://docs.streamlit.io/develop/quick-reference/release-notes/2024). This prevents deploying a version that cannot render the app.
- .env.example: appended optional settings without changing supplied entries.
- .gitignore: appended exclusions for the local Python 3.12 environment and runtime audio. Static audio remains eligible for git.

No supplied lesson/scenario wording or existing public function signatures were changed. Existing misplaced files were renamed as documented above.

Demo storage uses SQLAlchemy/SQLite; optional PostgreSQL support enables row-level security on application tables to prevent public Supabase Data API access. Runtime audio is scoped by user and removed on account deletion. Session tokens are hashed in storage, expire after 14 days, and are omitted from sharing URLs.

The fake rehearsal reuses a supplied scenario. Fake coaching and scoring are labeled examples rather than evaluations. No paid AI calls were made during verification.
