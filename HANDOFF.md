# HANDOFF — Pre-built files are included

You are a senior full-stack engineer. The full product specification is in docs/SPEC.md.
Read docs/SPEC.md completely, then this file. This file OVERRIDES SPEC.md where they differ.
Follow SPEC.md PART 0 working rules (phases, tests, PROGRESS.md, DECISIONS.md, commits),
except that docs/SPEC.md already exists: do NOT overwrite it.

## 0. Inventory check (do this FIRST, before any code)
1. List every file currently in the repository.
2. The files PROVIDED by the project team are exactly:
   requirements.txt, requirements-dev.txt, pyproject.toml, .gitignore, .env.example,
   .streamlit/config.toml, .streamlit/secrets.toml.example, docs/SPEC.md, HANDOFF.md,
   core/__init__.py, core/config.py, core/pronunciation.py, core/srs.py,
   core/workdays.py, core/scoring.py, core/patterns.py, core/privacy.py,
   tests/__init__.py, tests/test_pronunciation.py, tests/test_srs.py,
   tests/test_workdays.py, tests/test_scoring.py, tests/test_patterns.py,
   tests/test_privacy.py,
   data/call_scenarios.json, data/badges.json, data/holidays.json,
   data/import/lessons_01_10.json, data/import/lessons_11_20.json,
   data/import/lessons_21_30.json.
3. Everything else in SPEC PART 4 is yours to create, INCLUDING app.py, views/,
   components/, services/, scripts/, the remaining core modules
   (core/prompts.py, core/ai_schemas.py, core/content.py, core/db.py, core/repo.py,
   core/auth.py, core/llm.py, core/fakes.py, core/speech.py, core/i18n.py,
   core/analytics.py, core/rate_limit.py, core/profile.py, core/mistakes.py,
   core/adaptivity.py), the remaining tests and docs, AGENTS.md and Makefile.
4. Write the result of this check at the top of docs/PROGRESS.md. If a provided file is
   missing or malformed, report it clearly and continue; do NOT invent replacement content
   for missing lesson or scenario files.

## 1. Provided files are AUTHORITATIVE
Do NOT rewrite or regenerate the provided files listed in section 0.2.
Rules:
- You MAY add new functions/modules and extend provided files (new helpers, new settings
  fields, new tests).
- You MAY fix genuine bugs (failing provided tests, crashes, schema mismatches). For every
  fix, record file, problem, change and reason in docs/DECISIONS.md.
- You MUST NOT change existing public function signatures or rewrite learning content text
  (Korean/English wording) except to fix a validation error; log any such change.
- You MUST NOT write new lessons or scenarios. Content creation is already done.

## 2. First steps (before Phase 0 work)
1. Do the inventory check (section 0).
2. Create AGENTS.md from SPEC PART 14 + the rules of this file.
3. Install requirements-dev.txt and run `pytest -q` on the provided tests. Fix only real
   bugs (log them in DECISIONS.md).
4. Commit "phase pre: inventory + verified provided core modules".

## 3. Overrides to SPEC.md
- core/calendar.py is replaced by core/workdays.py (avoids shadowing Python's stdlib
  `calendar`); tests/test_calendar.py is replaced by the provided tests/test_workdays.py.
  Use: load_holidays, is_working_day, lesson_day_for, lesson_date_for, current_streak,
  longest_streak, program_week. Streak input = set of dates where the user completed THAT
  day's lesson on that day (lesson_completions.on_time = 1). Holidays: data/holidays.json
  filtered by settings.holiday_countries (default VN). holidays.json may be partial.
- Phase 2 (Content) is REDEFINED as "Content import & validation" and MUST be done:
  a) scripts/merge_lessons.py: merge data/import/lessons_*.json → data/daily_lessons.json
     (sorted by day, exactly 30 lessons = 6 weeks × 5, fail on duplicates/gaps).
     Run it and commit the output.
  b) Write core/content.py with pydantic models DERIVED FROM THE ACTUAL JSON FILES (the
     models must fit the JSON; never edit the JSON to fit the models except genuine
     errors, logged in DECISIONS.md) plus cached loaders.
  c) Write scripts/validate_content.py per SPEC PART 9.6, and also check: every
     konglish_tip.pattern_key passes core.patterns.is_valid_key; every suggested_call_id
     exists; persona voices are in config.ALLOWED_VOICES; multi_party voices differ;
     mcq answer_index in range; no duplicate phrases/terms/tips across all 30 lessons.
  d) tests/test_content.py runs the validator logic.
- Pattern keys: core/patterns.py is the single source of truth (53 keys). It differs
  slightly from SPEC 9.5; follow patterns.py. Persona pressure points use
  patterns.pressure_point_for().
- Lesson schema notes: konglish_tip.category ∈ konglish|grammar|politeness|preposition|
  article|tense (word-choice tips use "grammar"); mini_quiz items use either question_en
  or question_ko; fill_blank items use sentence_en; terms = {common: 1 term,
  Audit/Tax/Deals/Advisory: 2 terms each}.
- Prompts: write core/prompts.py and core/ai_schemas.py per SPEC PART 10–11. ALL AI calls
  use these prompt functions and pydantic models. Add deterministic fakes in
  core/fakes.py returning valid instances of every schema (SPEC 6.4). Never inline prompt
  text elsewhere.
- Privacy: use core/privacy.detect_sensitive() before rehearsal generation and Ask Jamie.
- Scoring/badges: use core/scoring.call_overall_score() and earned_badges(LearnerStats).
  data/badges.json holds display text only (icon, names, descriptions).
- Settings: always use core/config.get_settings(); costs via config.estimate_cost().

## 4. Then implement
Implement SPEC.md PART 15 phases in order: 0, 1 (skip modules already provided),
2 (as redefined in section 3), 3, 4, 5, 6, 7, 8 — with ruff + pytest + smoke test +
PROGRESS.md + commit after each phase. Respect the scope priority in section 6.9.
Finish with the SPEC PART 17 final report, including a list of any changes made to
provided files and any features skipped.

## 5. If you run out of context/time
Finish the current phase cleanly, commit, update docs/PROGRESS.md, and state where to
resume. The resume prompt will be: "Read HANDOFF.md, docs/SPEC.md, AGENTS.md and
docs/PROGRESS.md, run tests, and resume from the first incomplete phase."

## 6. Final adjustments (override SPEC.md)

### 6.1 Program length = 30 lessons (6 weeks)
Merge lessons_01_10, lessons_11_20 and lessons_21_30 into data/daily_lessons.json.
Keep every "30 lessons" requirement from SPEC.md. Beyond day 30 → "프로그램 완료" state.

### 6.2 Validation rule for voicemail
call_type "voicemail": curveballs may be empty (0–3), hidden_facts may be empty,
max_turns = 1. Other call types: curveballs 1–3.

### 6.3 Audio caching for Streamlit Cloud
Static, pre-generated audio (lesson content, opening lines, key phrases) is written to
audio_cache/static/ and COMMITTED to git. Runtime TTS goes to audio_cache/dynamic/
(git-ignored). speech.synthesize() checks static first, then dynamic.
pregenerate_audio.py writes to audio_cache/static/.

### 6.4 Two model tiers and cost accuracy
- Add OPENAI_MODEL_STRONG (default "gpt-4o") used ONLY for: call evaluator,
  custom_scenario (rehearsal builder), weekly report, cohort report. Everything else uses
  OPENAI_MODEL. Add matching env-overridable prices and use the correct price per call.
- TTS cost: for gpt-4o-mini-tts estimate by audio minutes (≈ 900 characters per minute,
  PRICE_TTS_PER_MINUTE default 0.015); keep per-character pricing for tts-1.
- Add OPENAI_STT_MODEL_SHADOWING (default = OPENAI_STT_MODEL) used only for shadowing and
  term pronunciation. Use temperature 0 and never pass the target sentence as a prompt hint.

### 6.5 Session link safety
Keep the session token in st.query_params["s"], but add a sidebar button
"🔗 공유용 링크 복사" showing the app URL WITHOUT the token, with the caption:
"주소창 링크에는 로그인 정보가 포함되어 있어요. 공유할 때는 공유용 링크를 사용해 주세요."
Token expiry: 14 days.

### 6.6 Configuration warnings
If PROGRAM_START_DATE is not set, show a red warning on the admin page. Add
`program_start_configured: bool` to Settings without changing existing signatures.

### 6.7 Languages
Korean and English must be complete on every page. Vietnamese is required only for
로드맵 and 관리자; elsewhere missing "vi" keys fall back to "en". test_i18n.py: ko and en
complete; vi complete for roadmap/admin keys.

### 6.8 Deployment notes for README / DEMO_RUNBOOK
- Streamlit Community Cloud: choose Python 3.11 in Advanced settings.
- Supabase: Singapore region; connection pooler URL as postgresql+psycopg://...;
  free projects pause after about a week of inactivity.
- DEMO_RUNBOOK: open the app 10 minutes before the demo (cold start), log in the seeded
  demo user on two tabs, keep FAKE_AI ready as a fallback.

### 6.9 Scope priority (if quota runs low, stop after SHOULD)
- MUST: inventory + content import/validation, auth/onboarding, 오늘의 학습 ①–⑦,
  모의 통화 (library + ✨ rehearsal), Jamie daily card, 약점 노트, 로드맵, basic 관리자
  (users, DAU, retention, completion, call scores, cost), seed_demo.py, FAKE_AI mode,
  smoke test.
- SHOULD: 복습, 코치에게 물어보기, feedback widget, basic 내 기록 (metrics + settings +
  data deletion).
- COULD: 주간 퀴즈, 지난 학습, weekly AI report, 그룹 인사이트, pulse surveys, badges grid,
  heatmap.
Build MUST features first, then SHOULD, then COULD. Record what was skipped in the final
report.