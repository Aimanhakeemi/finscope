"""Transaction categorizer: local sklearn model + rules + optional Claude fallback.

Skeleton — the training / persistence details live in docs/ML.md. The public
surface is `categorize_many(descriptions, amounts) -> list[Prediction]`.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass

TAXONOMY = [
    "groceries", "dining", "coffee", "transport", "fuel", "utilities",
    "rent_mortgage", "subscriptions", "shopping", "health", "entertainment",
    "income", "other",
]

# High-precision merchant rules applied before the model.
RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"payroll|direct dep|salary", re.I), "income"),
    (re.compile(r"netflix|spotify|hulu|disney\+|nyt|new york times|icloud", re.I), "subscriptions"),
    (re.compile(r"apartments|property mgmt|mortgage|greenfield", re.I), "rent_mortgage"),
    (re.compile(r"starbucks|blue bottle|coffee|philz|peet", re.I), "coffee"),
    (re.compile(r"shell|chevron|exxon|76 |bp #|gas station", re.I), "fuel"),
    (re.compile(r"uber|lyft|transit|mta|bart|caltrain", re.I), "transport"),
    (re.compile(r"water|power|electric|pg&e|comcast|xfinity|state farm", re.I), "utilities"),
    (re.compile(r"whole foods|trader joe|safeway|kroger|aldi|grocer", re.I), "groceries"),
    (re.compile(r"cvs|walgreens|pharmacy|clinic|dental|fitness", re.I), "health"),
]

CONFIDENCE_THRESHOLD = 0.55  # tuned in docs/eval_report.md


@dataclass(frozen=True)
class Prediction:
    category: str
    confidence: float
    source: str  # "rule" | "model" | "llm"


def _rule_match(description: str) -> str | None:
    for pattern, cat in RULES:
        if pattern.search(description):
            return cat
    return None


class Categorizer:
    def __init__(self, model_path: str = "app/artifacts/categorizer.joblib") -> None:
        self._model = None
        self._model_path = model_path

    def _load(self):
        if self._model is None:
            import joblib  # lazy import so tests that only hit rules stay light

            self._model = joblib.load(self._model_path)
        return self._model

    def predict_one(self, description: str, amount: float) -> Prediction:
        rule = _rule_match(description)
        if rule:
            return Prediction(rule, 1.0, "rule")

        model = self._load()
        proba = model.predict_proba([description])[0]
        idx = int(proba.argmax())
        top_p = float(proba[idx])
        category = model.classes_[idx]

        if top_p >= CONFIDENCE_THRESHOLD or not os.getenv("ANTHROPIC_API_KEY"):
            return Prediction(category, top_p, "model")

        return _llm_classify(description, amount)


def _llm_classify(description: str, amount: float) -> Prediction:
    """Fallback to Claude for low-confidence rows. See docs/ML.md for the prompt."""
    from anthropic import Anthropic
    from anthropic.types import TextBlock

    client = Anthropic()
    msg = client.messages.create(
        model=os.getenv("FINSCOPE_LLM_MODEL", "claude-haiku-4-5-20251001"),
        max_tokens=16,
        temperature=0,
        system=(
            "You label bank transactions. Reply with EXACTLY one of: "
            + ", ".join(TAXONOMY)
        ),
        messages=[{"role": "user", "content": f"{description!r} amount {amount:.2f}"}],
    )
    block = msg.content[0] if msg.content else None
    label = block.text.strip().lower() if isinstance(block, TextBlock) else "other"
    if label not in TAXONOMY:
        label = "other"
    return Prediction(label, 0.5, "llm")
