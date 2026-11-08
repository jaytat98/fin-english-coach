"""One gateway for prompts, schemas, privacy checks, quotas, and cost logging."""

from uuid import uuid4

from core import db
from core.ai_schemas import SCHEMAS
from core.auth import now
from core.config import estimate_cost, get_settings, model_for
from core.fakes import response_for
from core.privacy import detect_sensitive
from core.prompts import messages_for
from core.rate_limit import reserve


class AIUnavailable(RuntimeError):
    pass


def generate(operation: str, context: dict, user: dict):
    settings = get_settings()
    if operation not in SCHEMAS:
        raise ValueError("Unsupported operation")
    if operation in ("custom_scenario", "ask_coach"):
        if detect_sensitive(context.get("text", "")):
            raise ValueError("sensitive_content")
    if not settings.ai_enabled:
        raise AIUnavailable("ai_unavailable")
    if operation == "ask_coach":
        reserve(user["id"], operation, settings.limits.ask_coach_per_day)
    if operation == "custom_scenario":
        reserve(user["id"], operation, settings.limits.custom_scenarios_per_day)
    if operation == "writing":
        reserve(
            user["id"], f"writing:{context.get('day')}", settings.limits.writing_attempts_per_lesson
        )
    reserve(user["id"], "ai", settings.limits.ai_calls_per_day)
    model, prices = model_for(operation)
    if settings.fake_ai:
        result = response_for(operation, context, user["language"])
        cost = 0.0
    else:
        from openai import OpenAI

        try:
            client = OpenAI(api_key=settings.openai_api_key, timeout=45, max_retries=1)
            response = client.chat.completions.create(
                model=model,
                messages=messages_for(operation, context, user["language"]),
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=4000,
            )
            # Record actual API usage even if the response subsequently fails validation.
            cost = (
                estimate_cost(
                    prices, response.usage.prompt_tokens, response.usage.completion_tokens
                )
                if response.usage
                else 0.0
            )
            log_usage(user["id"], operation, model, cost, False)
            result = SCHEMAS[operation].model_validate_json(
                response.choices[0].message.content or ""
            )
        except Exception as error:
            raise AIUnavailable("ai_failed") from error
        return result
    log_usage(user["id"], operation, model, cost, True)
    return result


def log_usage(user_id, operation, model, cost, fake):
    with db.get_engine().begin() as connection:
        connection.execute(
            db.usage.insert().values(
                id=uuid4().hex,
                user_id=user_id,
                operation=operation,
                model=model,
                cost=cost,
                fake=int(fake),
                created_at=now(),
            )
        )
