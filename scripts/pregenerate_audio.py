"""Prepare static audio from supplied content. Default is a no-cost dry run."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import COACH_VOICE, estimate_cost, get_settings  # noqa: E402
from core.content import load_lessons, load_scenarios  # noqa: E402
from core.speech import CACHE, cache_key, synthesize  # noqa: E402


def audio_items():
    items = set()
    for lesson in load_lessons():
        items.add((lesson.speaking_sentence.en, COACH_VOICE))
        for example in lesson.phrase.examples:
            items.add((example.en, COACH_VOICE))
        for term in lesson.terms.all_terms():
            items.add((term.term, COACH_VOICE))
    for scenario in load_scenarios():
        for persona in scenario.personas:
            items.add((persona.opening_line, persona.voice))
        for phrase in scenario.key_phrases:
            items.add((phrase.en, COACH_VOICE))
    return sorted(items)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--generate", action="store_true", help="Make paid TTS calls for missing audio"
    )
    args = parser.parse_args()
    settings = get_settings()
    missing = [
        (text, voice)
        for text, voice in audio_items()
        if not (CACHE / "static" / cache_key(text, settings.tts_model, voice)).exists()
    ]
    cost = estimate_cost(settings.prices, tts_chars=sum(len(text) for text, _ in missing))
    print(f"Missing static clips: {len(missing)}. Estimated cost: ${cost:.4f}.")
    if args.generate:
        if settings.fake_ai or not settings.openai_api_key:
            parser.error("Generation requires OPENAI_API_KEY and FAKE_AI=0")
        for index, (text, voice) in enumerate(missing, 1):
            synthesize(text, voice, static=True)
            print(f"Generated {index}/{len(missing)}")
    else:
        print("Dry run only. Use --generate to create audio_cache/static/*.mp3, then commit it.")


if __name__ == "__main__":
    main()
