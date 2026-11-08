"""Check actual content and reject corruption without modifying supplied files."""

import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from core.content import (
    Lesson,
    Scenario,
    load_lessons,
    load_scenarios,
    validate_content,
    validate_files,
)
from scripts.merge_lessons import merge_lessons

ROOT = Path(__file__).resolve().parents[1]


def lesson_data():
    return json.loads((ROOT / "data/daily_lessons.json").read_text())[0]


def scenario_data(kind="phone"):
    return next(
        row
        for row in json.loads((ROOT / "data/call_scenarios.json").read_text())
        if row["call_type"] == kind
    )


def test_supplied_content_passes():
    assert validate_files() == (30, 12)


def test_merge_preserves_every_supplied_record(tmp_path):
    output = tmp_path / "merged.json"
    merged = merge_lessons(ROOT / "data/import", output)
    supplied = sum(
        [json.loads(path.read_text()) for path in sorted((ROOT / "data/import").glob("*.json"))],
        [],
    )
    assert merged == sorted(supplied, key=lambda row: row["day"])
    committed = json.loads((ROOT / "data/daily_lessons.json").read_text())
    assert json.loads(output.read_text()) == committed


@pytest.mark.parametrize("bad_days", [[], list(range(1, 30)), list(range(1, 30)) + [29]])
def test_merge_rejects_gaps_duplicates_without_overwriting(tmp_path, bad_days):
    source = tmp_path / "source"
    source.mkdir()
    batch = [{"day": day} for day in bad_days]
    (source / "lessons_batch.json").write_text(json.dumps(batch))
    output = tmp_path / "merged.json"
    output.write_text("preserve existing output")
    with pytest.raises(ValueError, match="duplicates or gaps"):
        merge_lessons(source, output)
    assert output.read_text() == "preserve existing output"


@pytest.mark.parametrize("field,value", [("week", 6), ("day", True)])
def test_invalid_day_or_week(field, value):
    data = lesson_data()
    data[field] = value
    with pytest.raises(ValidationError):
        Lesson.model_validate(data)


def test_invalid_pattern():
    data = lesson_data()
    data["konglish_tip"]["pattern_key"] = "unknown:pattern"
    with pytest.raises(ValidationError, match="Unknown pattern"):
        Lesson.model_validate(data)


@pytest.mark.parametrize("index", [-1, 4, True])
def test_invalid_quiz_answer(index):
    data = lesson_data()
    data["mini_quiz"][0]["answer_index"] = index
    with pytest.raises(ValidationError):
        Lesson.model_validate(data)


def test_mcq_requires_question():
    data = lesson_data()
    del data["mini_quiz"][0]["question_ko"]
    with pytest.raises(ValidationError, match="mcq needs"):
        Lesson.model_validate(data)


def test_fill_blank_requires_sentence():
    data = lesson_data()
    del data["mini_quiz"][1]["sentence_en"]
    with pytest.raises(ValidationError, match="fill_blank needs"):
        Lesson.model_validate(data)


def test_unknown_scenario_reference():
    lessons = list(load_lessons())
    lessons[0] = lessons[0].model_copy(update={"suggested_call_id": "missing"})
    with pytest.raises(ValueError, match="unknown suggested_call_id"):
        validate_content(tuple(lessons), load_scenarios())


@pytest.mark.parametrize("kind", ["phrase", "term", "tip"])
def test_duplicate_content(kind):
    lessons = list(load_lessons())
    data = lessons[1].model_dump(by_alias=True)
    first = lessons[0].model_dump(by_alias=True)
    if kind == "phrase":
        data["phrase"]["text"] = first["phrase"]["text"].upper()
    elif kind == "term":
        data["terms"]["common"]["term"] = first["terms"]["Audit"][0]["term"]
    else:
        data["konglish_tip"]["wrong"] = first["konglish_tip"]["wrong"]
    lessons[1] = Lesson.model_validate(data)
    with pytest.raises(ValueError, match=f"duplicate {kind}"):
        validate_content(tuple(lessons), load_scenarios())


def test_duplicate_scenario_ids():
    scenarios = load_scenarios()
    with pytest.raises(ValueError, match="unique IDs"):
        validate_content(load_lessons(), scenarios + (scenarios[0],))


def test_invalid_voice():
    data = scenario_data()
    data["personas"][0]["voice"] = "invalid"
    with pytest.raises(ValidationError, match="Unsupported persona voice"):
        Scenario.model_validate(data)


def test_multi_party_voices_must_differ():
    data = scenario_data("multi_party")
    data["personas"][1]["voice"] = data["personas"][0]["voice"]
    with pytest.raises(ValidationError, match="different voices"):
        Scenario.model_validate(data)


def test_voicemail_exceptions():
    data = scenario_data("voicemail")
    data["curveballs"] = []
    for persona in data["personas"]:
        persona["hidden_facts"] = []
    assert Scenario.model_validate(data).max_turns == 1
    data["max_turns"] = 2
    with pytest.raises(ValidationError, match="max_turns"):
        Scenario.model_validate(data)


def test_regular_calls_need_curveballs():
    data = scenario_data()
    data["curveballs"] = []
    with pytest.raises(ValidationError, match="curveballs"):
        Scenario.model_validate(data)


def test_cached_models_are_immutable():
    lesson = load_lessons()[0]
    with pytest.raises(ValidationError):
        lesson.phrase.text = "changed"
    assert isinstance(lesson.mini_quiz, tuple)


def test_validator_reads_changed_files_even_after_loader_cache(tmp_path):
    load_lessons()
    for name in ("daily_lessons.json", "call_scenarios.json"):
        (tmp_path / name).write_bytes((ROOT / "data" / name).read_bytes())
    data = json.loads((tmp_path / "daily_lessons.json").read_text())
    data[0] = copy.deepcopy(data[1])
    (tmp_path / "daily_lessons.json").write_text(json.dumps(data))
    with pytest.raises(ValueError, match="days 1–30"):
        validate_files(tmp_path)
