"""Railtracks evaluation setup for the daily insight agent.

Metrics target the agent's specific failure modes (strict per-line output
format, factual grounding against the tool output) rather than the generic
helpfulness/efficiency that the railtracks quickstart shows.
"""

from __future__ import annotations

import os

import railtracks as rt
from railtracks import evaluations as evals


# Same default as the agent — when LLM_MODEL/EVAL_JUDGE_MODEL is set, override.
_DEFAULT_JUDGE_MODEL = "claude-haiku-4-5-20251001"


FORMAT_COMPLIANCE = evals.metrics.Categorical(
    name="FormatCompliance",
    description=(
        "Does the agent's final response follow the strict format: one line per "
        "metric, no markdown, no preamble, format `{metric}: {one-sentence "
        "insight with latest value and trend}`? "
        "Compliant = every line conforms. "
        "MinorDeviation = mostly conforms but one stray formatting element "
        "(extra blank line, single missing colon, etc.). "
        "MajorDeviation = bullets, headers, prose paragraphs, multi-line "
        "insights per metric."
    ),
    categories=["Compliant", "MinorDeviation", "MajorDeviation"],
)


FACTUAL_GROUNDING = evals.metrics.Categorical(
    name="FactualGrounding",
    description=(
        "Is every numeric value and trend statement in the agent's final "
        "response actually present in the get_recent_metrics tool output? "
        "Inspect the tool calls and tool outputs in the data. "
        "FullyGrounded = every claim traceable to the tool data. "
        "PartiallyGrounded = some values right, some invented or wrong. "
        "Hallucinated = at least one fabricated value or trend."
    ),
    categories=["FullyGrounded", "PartiallyGrounded", "Hallucinated"],
)


def build_evaluators() -> list:
    """Return the evaluator list to run against each daily-insight session.

    The judge model defaults to the agent's own model; override via
    EVAL_JUDGE_MODEL (otherwise LLM_MODEL, otherwise the constant default).
    """
    judge_model = (
        os.environ.get("EVAL_JUDGE_MODEL", "").strip()
        or os.environ.get("LLM_MODEL", "").strip()
        or _DEFAULT_JUDGE_MODEL
    )
    return [
        evals.ToolUseEvaluator(),
        evals.LLMInferenceEvaluator(),
        evals.JudgeEvaluator(
            llm=rt.llm.AnthropicLLM(judge_model),
            metrics=[FORMAT_COMPLIANCE, FACTUAL_GROUNDING],
            reasoning=True,
        ),
    ]
