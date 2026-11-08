import pytest

from core import db, repo
from core.ai_schemas import SCHEMAS
from core.config import Prices, estimate_cost, get_settings, model_for
from core.content import load_scenarios
from core.fakes import response_for
from core.llm import generate


@pytest.mark.parametrize("operation", list(SCHEMAS))
def test_all_fake_schemas(operation):
    context = {
        "scenario": load_scenarios()[0].model_dump(by_alias=True),
        "transcript": [],
        "text": "A fictional deadline discussion",
        "sample_answer": "Let's circle back.",
    }
    result = response_for(operation, context, "en")
    assert isinstance(result, SCHEMAS[operation])


def test_privacy_check_precedes_quota_and_generation(learner):
    with pytest.raises(ValueError, match="sensitive_content"):
        generate("ask_coach", {"text": "Email me at private@example.com"}, learner)
    assert repo.rows(db.limits, learner["id"]) == []
    assert repo.rows(db.usage, learner["id"]) == []


def test_fake_generation_records_zero_cost(learner):
    result = generate("writing", {"text": "A test", "day": 1}, learner)
    assert "Demo" in result.message
    assert repo.rows(db.usage, learner["id"])[0]["cost"] == 0


def test_model_tiers(storage):
    assert model_for("call_turn")[0] == "gpt-4o-mini"
    for operation in ("call_evaluator", "custom_scenario", "weekly_report", "cohort_report"):
        model, prices = model_for(operation)
        assert model == "gpt-4o"
        assert estimate_cost(prices, tokens_in=1_000_000, tokens_out=1_000_000) == 12.5
    assert get_settings().program_start_configured


def test_tts_cost_modes():
    assert estimate_cost(Prices(tts_by_minute=True), tts_chars=900) == 0.015
    assert estimate_cost(Prices(), tts_chars=1_000_000) == 15
