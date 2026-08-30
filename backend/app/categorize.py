"""Transaction categorizer: local sklearn model plus deterministic rules.

Skeleton — the training / persistence details live in docs/ML.md. The public
surface is `categorize_many(descriptions, amounts) -> list[Prediction]`.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from app.etl import clean_merchant

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
DEFAULT_MODEL_PATH = Path(__file__).resolve().parent / "artifacts" / "categorizer.joblib"


@dataclass(frozen=True)
class Prediction:
    category: str
    confidence: float
    source: str  # "rule" | "model"
    low_confidence: bool = False


def _rule_match(description: str) -> str | None:
    for pattern, cat in RULES:
        if pattern.search(description):
            return cat
    return None


class Categorizer:
    def __init__(self, model_path: str | Path = DEFAULT_MODEL_PATH) -> None:
        self._model = None
        self._model_path = Path(model_path)

    def train(self, df: pd.DataFrame) -> None:
        """Train and persist the documented character n-gram classifier."""
        if "merchant" in df:
            merchants = df["merchant"].astype(str)
        elif "description" in df:
            merchants = df["description"].map(clean_merchant)
        else:
            raise ValueError("training data needs a merchant or description column")
        if "category" not in df:
            raise ValueError("training data needs a category column")
        labels = df["category"].astype(str)
        invalid = sorted(set(labels) - set(TAXONOMY))
        if invalid:
            raise ValueError(f"unknown categories: {invalid}")
        if labels.nunique() < 2:
            raise ValueError("training data needs at least two categories")

        model = Pipeline(
            [
                ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))),
                (
                    "classifier",
                    LogisticRegression(max_iter=1000, class_weight="balanced"),
                ),
            ]
        )
        model.fit(merchants, labels)
        self._model_path.parent.mkdir(parents=True, exist_ok=True)
        import joblib

        joblib.dump(model, self._model_path)
        self._model = model

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
        proba = model.predict_proba([clean_merchant(description)])[0]
        idx = int(proba.argmax())
        top_p = float(proba[idx])
        classifier = model.named_steps["classifier"] if hasattr(model, "named_steps") else model
        category = str(classifier.classes_[idx])

        return Prediction(category, top_p, "model", top_p < CONFIDENCE_THRESHOLD)


def categorize_many(
    descriptions: list[str], amounts: list[float], categorizer: Categorizer | None = None
) -> list[Prediction]:
    if len(descriptions) != len(amounts):
        raise ValueError("descriptions and amounts must have the same length")
    categorizer = categorizer or Categorizer()
    return [
        categorizer.predict_one(description, amount)
        for description, amount in zip(descriptions, amounts)  # noqa: B905
    ]
