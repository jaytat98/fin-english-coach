"""Validated content models derived from the supplied JSON, not an invented spec."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator

from core.config import ALLOWED_VOICES
from core.patterns import is_valid_key

DATA = Path(__file__).resolve().parents[1] / "data"
Text = Annotated[str, Field(min_length=1)]


class ContentModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Translation(ContentModel):
    en: Text
    ko: Text


class Phrase(ContentModel):
    text: Text
    meaning_ko: Text
    nuance_ko: Text
    register_: Text = Field(alias="register")
    examples: tuple[Translation, ...] = Field(min_length=1)


class Term(ContentModel):
    term: Text
    meaning_ko: Text
    definition_en: Text
    example_en: Text
    example_ko: Text


class Terms(ContentModel):
    common: Term
    Audit: tuple[Term, Term]
    Tax: tuple[Term, Term]
    Deals: tuple[Term, Term]
    Advisory: tuple[Term, Term]

    def all_terms(self) -> tuple[Term, ...]:
        return (self.common, *self.Audit, *self.Tax, *self.Deals, *self.Advisory)


class Tip(ContentModel):
    category: Literal["konglish", "grammar", "politeness", "preposition", "article", "tense"]
    pattern_key: Text
    title_ko: Text
    wrong: Text
    right: Text
    explanation_ko: Text

    @model_validator(mode="after")
    def valid_pattern(self):
        if not is_valid_key(self.pattern_key):
            raise ValueError(f"Unknown pattern key: {self.pattern_key}")
        return self


class SpeakingSentence(Translation):
    situation_ko: Text


class WritingTask(ContentModel):
    instruction_ko: Text
    target_phrase: Text
    sample_answer: Text


class QuizItem(ContentModel):
    type: Literal["mcq", "fill_blank"]
    question_en: Text | None = None
    question_ko: Text | None = None
    sentence_en: Text | None = None
    options: tuple[Text, ...] = Field(min_length=2)
    answer_index: int = Field(ge=0, strict=True)
    explanation_ko: Text

    @model_validator(mode="after")
    def valid_question(self):
        if self.answer_index >= len(self.options):
            raise ValueError("answer_index is outside options")
        if self.type == "mcq" and not (self.question_en or self.question_ko):
            raise ValueError("mcq needs question_en or question_ko")
        if self.type == "fill_blank" and not self.sentence_en:
            raise ValueError("fill_blank needs sentence_en")
        return self


class Lesson(ContentModel):
    day: int = Field(ge=1, le=30, strict=True)
    week: int = Field(ge=1, le=6, strict=True)
    theme_ko: Text
    theme_en: Text
    phrase: Phrase
    terms: Terms
    konglish_tip: Tip
    speaking_sentence: SpeakingSentence
    writing_task: WritingTask
    mini_quiz: tuple[QuizItem, ...] = Field(min_length=1)
    suggested_call_id: Text
    review_status: Text

    @model_validator(mode="after")
    def valid_week(self):
        if self.week != (self.day - 1) // 5 + 1:
            raise ValueError("week does not match lesson day")
        return self


class Persona(ContentModel):
    name: Text
    title: Text
    company_fictional: Text
    voice: Text
    personality_en: Text
    speaking_style_en: Text
    hidden_facts: tuple[Text, ...]
    opening_line: Text

    @model_validator(mode="after")
    def valid_voice(self):
        if self.voice not in ALLOWED_VOICES:
            raise ValueError(f"Unsupported persona voice: {self.voice}")
        return self


class Goal(ContentModel):
    id: Text
    text_ko: Text
    text_en: Text
    success_criteria_en: Text


class Scenario(ContentModel):
    id: Text
    title_ko: Text
    title_en: Text
    service_line: Literal["General", "Audit", "Tax", "Deals", "Advisory"]
    difficulty_default: Literal["easy", "medium", "hard"]
    call_type: Literal["phone", "video", "multi_party", "voicemail"]
    target_minutes: float = Field(gt=0)
    briefing_ko: Text
    user_role_ko: Text
    personas: tuple[Persona, ...] = Field(min_length=1)
    goals: tuple[Goal, ...] = Field(min_length=1)
    curveballs: tuple[Text, ...] = Field(max_length=3)
    key_phrases: tuple[Translation, ...] = Field(min_length=1)
    max_turns: int = Field(ge=1, strict=True)
    closing_condition_en: Text

    @model_validator(mode="after")
    def valid_call(self):
        if self.call_type == "voicemail":
            if self.max_turns != 1:
                raise ValueError("voicemail max_turns must be 1")
        elif not self.curveballs or any(not p.hidden_facts for p in self.personas):
            raise ValueError("Non-voicemail calls need curveballs and persona hidden facts")
        if self.call_type == "multi_party":
            voices = {p.voice for p in self.personas}
            if len(self.personas) < 2 or len(voices) != len(self.personas):
                raise ValueError("multi_party needs multiple personas with different voices")
        if len({g.id for g in self.goals}) != len(self.goals):
            raise ValueError("Duplicate goal IDs")
        return self


@lru_cache(maxsize=8)
def load_lessons(path: Path = DATA / "daily_lessons.json") -> tuple[Lesson, ...]:
    return TypeAdapter(tuple[Lesson, ...]).validate_json(Path(path).read_text(encoding="utf-8"))


@lru_cache(maxsize=8)
def load_scenarios(path: Path = DATA / "call_scenarios.json") -> tuple[Scenario, ...]:
    return TypeAdapter(tuple[Scenario, ...]).validate_json(Path(path).read_text(encoding="utf-8"))


def validate_content(lessons: tuple[Lesson, ...], scenarios: tuple[Scenario, ...]) -> None:
    """Cross-record checks explicitly required by HANDOFF.md; raise on any error."""
    if [lesson.day for lesson in lessons] != list(range(1, 31)):
        raise ValueError("Lessons must be sorted, exactly days 1–30, without duplicates or gaps")
    ids = [scenario.id for scenario in scenarios]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("Scenarios must be nonempty and have unique IDs")
    seen: dict[str, set[str]] = {"phrase": set(), "term": set(), "tip": set()}
    for lesson in lessons:
        if lesson.suggested_call_id not in ids:
            raise ValueError(f"Day {lesson.day}: unknown suggested_call_id")
        values = [("phrase", lesson.phrase.text), ("tip", lesson.konglish_tip.wrong)]
        values.extend(("term", term.term) for term in lesson.terms.all_terms())
        for kind, value in values:
            normalized = " ".join(value.casefold().split())
            if normalized in seen[kind]:
                raise ValueError(f"Day {lesson.day}: duplicate {kind}: {value}")
            seen[kind].add(normalized)


def validate_files(data_dir: Path = DATA) -> tuple[int, int]:
    """Always read fresh files for validation, independent of loader caches."""
    lessons = TypeAdapter(tuple[Lesson, ...]).validate_python(
        json.loads((data_dir / "daily_lessons.json").read_text(encoding="utf-8"))
    )
    scenarios = TypeAdapter(tuple[Scenario, ...]).validate_python(
        json.loads((data_dir / "call_scenarios.json").read_text(encoding="utf-8"))
    )
    validate_content(lessons, scenarios)
    return len(lessons), len(scenarios)
