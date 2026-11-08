# Demo runbook

## Ten minutes before the demo

Open the deployed app 10 minutes early to allow a Community Cloud cold start. Check that the database project is active; free Supabase projects may pause after about a week of inactivity. Use Python 3.11 in Streamlit Advanced settings and a Singapore Supabase project with a `postgresql+psycopg://` pooler URL for durable storage.

Keep `FAKE_AI="1"` ready as a fallback in Streamlit Secrets. Demo responses and scores must stay visibly labeled. With FAKE_AI enabled, click **Explore the demo**; this seeds the demo account idempotently. Open the same seeded demo user in two tabs using its session URL privately, then verify progress saved in one tab is visible after rerunning the other. Use the sidebar's **sharing link** for anyone else; it excludes the session token.

## Walkthrough

1. **Today's lesson:** select a past/current lesson. Read the phrase, service-line terms and mistake tip; mark each complete.
2. In **Speak aloud**, use text practice for offline mode. Real microphone transcription requires live AI. Explain that transcript matching is approximate, not a phoneme-level pronunciation assessment.
3. Write a sentence and request feedback. In fake mode the response explicitly identifies itself as a demo; self-review against the supplied example also works.
4. Answer both quiz questions, write a reflection, and finish the lesson. Refresh the second tab to confirm saved progress.
5. Open **Review**, reveal a card and choose a rating. The schedule persists.
6. Open **Mock calls**, start a library scenario, send a reply and end the call for feedback. Demo scores are examples.
7. Try **Rehearse my situation** with fictional details. In fake mode it selects supplied content, rather than claiming to generate a new scenario.
8. Open **My progress**, change language, export your data and leave feedback. Test deletion only with a disposable account; it also revokes sessions in the second tab.
9. Open **Admin**, enter the separate admin password and check users, DAU, retention, completion, real call-score aggregate and estimated cost. No production scores are inferred from fake calls.

## Live integration check

Set FAKE_AI=0 and a valid OpenAI key only when ready for paid calls. Verify one text feedback response, one short recorded WAV transcription, one TTS playback, and one call evaluation. An AI error must display an actionable message without losing the submitted call turn. Pending turns can be retried or the call can be ended. No live result has been verified in this development environment.

## Failure handling

- **No login/demo button:** set FAKE_AI=1 for the demo, or configure the pilot access code and create an account.
- **Database unavailable:** check the exact pooler host, password URL encoding, SSL parameter and project state. Do not paste secrets into chat or logs.
- **AI unavailable:** use fake mode or the supplied examples for self-review; never present fake scores as real assessments.
- **No audio:** text practice remains available. Pre-generated files can be generated later using `scripts/pregenerate_audio.py --generate` and committed under `audio_cache/static/`.
- **Program shows preview/completed:** inspect PROGRAM_START_DATE. Lessons follow working weekdays, with an explicit warning while the supplied holiday file is missing.
