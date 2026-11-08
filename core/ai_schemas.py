"""Validated response contracts for every AI operation used by the app."""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.content import Scenario
from core.patterns import is_valid_key


class AIModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Correction(AIModel):
    pattern_key: str
    wrong: str
    right: str
    explanation: str

    @field_validator("pattern_key")
    @classmethod
    def known_pattern(cls, value):
        if not is_valid_key(value):
            raise ValueError("Unknown mistake pattern")
        return value


class Feedback(AIModel):
    message: str = Field(min_length=1)
    improved: str
    corrections: list[Correction]


class CallTurn(AIModel):
    speaker: str
    text: str = Field(min_length=1, max_length=4000)
    finished: bool


class Scores(AIModel):
    task_completion: float = Field(ge=1, le=10)
    clarity: float = Field(ge=1, le=10)
    politeness_tone: float = Field(ge=1, le=10)
    handling_pushback: float = Field(ge=1, le=10)
    vocabulary: float = Field(ge=1, le=10)
    grammar: float = Field(ge=1, le=10)


class CallEvaluation(AIModel):
    scores: Scores
    summary: str
    next_step: str
    corrections: list[Correction]


class Rehearsal(AIModel):
    scenario: Scenario


SCHEMAS = {
    "writing": Feedback,
    "ask_coach": Feedback,
    "call_turn": CallTurn,
    "call_evaluator": CallEvaluation,
    "custom_scenario": Rehearsal,
}
