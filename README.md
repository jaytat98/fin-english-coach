# Jamie · Workplace English Coach

A Streamlit pilot app built around the team's 30 supplied lessons and 12 call scenarios. It includes seven-step daily learning, mock calls, rehearsal, spaced review, Ask Jamie, a mistake notebook, a six-week roadmap, personal records, and an admin dashboard.

## Run locally

Use Python **3.11** (3.12 is also tested locally).

```sh
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/merge_lessons.py
python scripts/validate_content.py
FAKE_AI=1 streamlit run app.py
```

Choose **Explore the demo**. No API key or signup is needed in explicitly enabled demo mode. The shared demo account contains fictional practice only; demo feedback and scores are labeled and excluded from live call-score analytics. With no configured start date, the demo starts on the current week's Monday so past lessons can be practiced.

To test actual signup, set `PILOT_ACCESS_CODE` and `ADMIN_PASSWORD` through your environment, `.env`, or an uncommitted `.streamlit/secrets.toml`. Passwords need at least 10 characters. `PROGRAM_START_DATE` determines the first program workday; future lessons are read-only previews. Session links expire after 14 days and can be revoked by signing out.

## Deploy a demo on Streamlit Community Cloud

1. Push this project to `jaytat98/fin-english-coach` on GitHub.
2. In Streamlit Community Cloud, choose **Create app**, select that repository and the branch containing these changes, and set the main file to **`app.py`**.
3. In **Advanced settings**, select **Python 3.11**.
4. Paste `.streamlit/secrets.demo.toml.example` into the Secrets box. Replace the passwords, `PROGRAM_START_DATE`, and `APP_URL` with your actual choices.
5. Deploy, open **Explore the demo**, and complete the checks in [DEMO_RUNBOOK.md](docs/DEMO_RUNBOOK.md).

The deploy form's Python/secrets options are documented in the [Streamlit deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy). Do not commit actual secret files.

SQLite makes the demo self-contained, but its files on Community Cloud are not durable storage for a real cohort. Use PostgreSQL for real learner data.

## Connect a real cohort

Create a Supabase project in **Singapore** and copy the exact **session pooler** connection string from **Connect**. Use the SQLAlchemy driver prefix `postgresql+psycopg://`, URL-encode special characters in the password, and append `?sslmode=require`. The example in `.streamlit/secrets.production.toml.example` shows the format; it is not a usable credential.

The app creates its tables at startup. Use a dedicated project or a database role that owns these app tables. PostgreSQL row-level security is enabled with no public policies, preventing anonymous Supabase Data API access; the trusted backend owner connection handles user-scoped queries. Prepared statements are disabled for compatibility with Supabase's shared transaction pooler as well. See [Supabase connection guidance](https://supabase.com/docs/guides/database/connecting-to-postgres).

Set `FAKE_AI="0"`, a valid `OPENAI_API_KEY`, unique pilot/admin passwords, a valid program start date, and the deployed `APP_URL`. Free Supabase projects may pause after about a week of inactivity; check the project's status before a demo.

```sh
python scripts/check_deploy.py --production
```

This checks configuration, content and DB connectivity without spending API credits. Then manually verify one real writing response, a recorded transcription, a TTS clip and a completed call. Local verification covers fake AI and mocked speech, not a live account or Supabase connection.

## Models, audio, and costs

All generated text uses `core/prompts.py`, Pydantic response schemas, and `core/llm.py`. Only call evaluation, custom rehearsal, and future weekly/cohort reports select `OPENAI_MODEL_STRONG`; other text tasks select `OPENAI_MODEL`. The defaults match HANDOFF; environment variables can change them. Official documentation currently marks GPT-4o as deprecated, so verify account availability before enabling live mode; this implementation does not silently substitute another model. See the [GPT-4o model page](https://developers.openai.com/api/docs/models/gpt-4o).

Cost entries are estimates. Strong-tier input/output prices and TTS minute pricing are configurable. `gpt-4o-mini-tts` estimates audio at 900 characters/minute; `tts-1` uses characters. Shadowing and term-pronunciation transcription select `OPENAI_STT_MODEL_SHADOWING`, use temperature zero, and never receive the target sentence as a prompt hint. Only shadowing is currently exposed as a dedicated recording exercise.

Audio reads `audio_cache/static/` before `audio_cache/dynamic/`. Dynamic audio is git-ignored. Pre-generate supplied content when a paid API key is available:

```sh
python scripts/pregenerate_audio.py               # no-cost estimate
FAKE_AI=0 python scripts/pregenerate_audio.py --generate
# Review and commit audio_cache/static/*.mp3.
```

No prerecorded audio was fabricated. Without a key, demo mode uses text practice and clearly reports that audio generation/transcription is unavailable.

## Verification

```sh
python -m pytest -q
python -m ruff check .
python scripts/smoke_test.py
python scripts/check_deploy.py
```

The smoke tests drive actual Streamlit widgets through sign-in, every page, lesson completion, review, a mock call and account deletion. GitHub Actions installs the full requirements and runs tests on Python 3.11/3.12. See [PROGRESS.md](docs/PROGRESS.md) for the exact local results and remaining gaps.

## Supplied-content limitations and scope

`docs/SPEC.md`, `data/holidays.json`, and `data/badges.json` were absent from the provided repository. No replacements were invented. Following the user's instruction to continue until deployable, the app uses the explicit requirements in HANDOFF and records assumptions in [DECISIONS.md](docs/DECISIONS.md).

- Without holiday data, scheduling uses weekdays and displays that limitation. Badge display is deferred.
- UI labels are Korean/English throughout, with Vietnamese for roadmap/admin and English fallback elsewhere. Supplied Korean-only quiz prompts/options and explanations remain verbatim; complete English learning-content localization requires approved translations.
- Weekly quizzes, weekly AI reports, group insights, pulse surveys, badge grids and heatmaps are deferred. No missing SPEC phase is claimed compliant.
- The app is ready for a configured **demo deployment**, not a claim of production security certification or a completed live-AI integration test.

Local `streamlit run` could not bind a port in this managed workspace. The Streamlit AppTest integration suite passed; verify the deployed URL after pushing from a writable Git environment.
