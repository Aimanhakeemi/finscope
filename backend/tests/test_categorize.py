from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd
from app.categorize import TAXONOMY, Categorizer


def test_rules_fire_before_the_model(tmp_path):
    model_path = tmp_path / "categorizer.joblib"
    categorizer = Categorizer(model_path)
    categorizer.train(
        pd.DataFrame(
            {
                "merchant": ["market", "restaurant", "bus", "clinic"],
                "category": ["groceries", "dining", "transport", "health"],
            }
        )
    )
    prediction = Categorizer(model_path).predict_one("STARBUCKS STORE 119", -6)
    assert prediction.category == "coffee"
    assert prediction.source == "rule"


def test_model_path_predicts_a_taxonomy_category(tmp_path):
    model_path = tmp_path / "categorizer.joblib"
    categorizer = Categorizer(model_path)
    categorizer.train(
        pd.DataFrame(
            {
                "merchant": ["market", "restaurant", "bus", "clinic"],
                "category": ["groceries", "dining", "transport", "health"],
            }
        )
    )
    prediction = Categorizer(model_path).predict_one("local market", -20)
    assert prediction.category in TAXONOMY
    assert 0 <= prediction.confidence <= 1


def test_low_confidence_stays_with_local_model():
    categorizer = Categorizer("unused.joblib")
    categorizer._model = SimpleNamespace(
        predict_proba=lambda _values: np.array([[0.2, 0.2, 0.2, 0.2, 0.2]]),
        named_steps={
            "classifier": SimpleNamespace(
                classes_=["coffee", "dining", "health", "other", "shopping"]
            )
        },
    )
    prediction = categorizer.predict_one("ambiguous merchant", -11)
    assert prediction.category == "coffee"
    assert prediction.confidence == 0.2
    assert prediction.source == "model"
