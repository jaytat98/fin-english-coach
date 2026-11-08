"""Deterministic, clearly labeled demo responses; never claim live assessment."""

from core.ai_schemas import CallEvaluation, CallTurn, Feedback, Rehearsal, Scores
from core.content import Scenario, load_scenarios


def response_for(operation, context, language):
    ko = language == "ko"
    message = (
        "데모 피드백입니다. 실제 AI 평가가 아닙니다. 예문과 비교해 보세요."
        if ko
        else "Demo feedback, not an AI assessment. Compare your answer with the example."
    )
    if operation in ("writing", "ask_coach"):
        return Feedback(message=message, improved=context.get("sample_answer", ""), corrections=[])
    if operation == "call_evaluator":
        return CallEvaluation(
            scores=Scores(**{key: 7 for key in Scores.model_fields}),
            summary=message,
            next_step=(
                "목표와 주요 표현을 다시 확인하세요." if ko else "Review the goals and key phrases."
            ),
            corrections=[],
        )
    if operation == "call_turn":
        scenario = Scenario.model_validate(context["scenario"])
        count = len([turn for turn in context["transcript"] if turn["role"] == "user"])
        persona = scenario.personas[count % len(scenario.personas)]
        text = (
            scenario.curveballs[(count - 1) % len(scenario.curveballs)]
            if scenario.curveballs
            else persona.opening_line
        )
        return CallTurn(
            speaker=persona.name, text=text, finished=count >= min(3, scenario.max_turns)
        )
    if operation == "custom_scenario":
        scenarios = load_scenarios()
        scenario = next(
            (s for s in scenarios if s.service_line == context.get("service_line")), scenarios[0]
        )
        return Rehearsal(scenario=scenario)
    raise ValueError(f"No fake for {operation}")
