from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pandas as pd
from anthropic.types import TextBlock
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


def test_low_confidence_uses_mocked_llm_and_invalid_labels_become_other(monkeypatch):
    categorizer = Categorizer("unused.joblib")
    categorizer._model = SimpleNamespace(
        predict_proba=lambda _values: np.array([[0.2, 0.2, 0.2, 0.2, 0.2]]),
        named_steps={
            "classifier": SimpleNamespace(
                classes_=["coffee", "dining", "health", "other", "shopping"]
            )
        },
    )
    response = SimpleNamespace(content=[TextBlock(type="text", text="not-a-category")])
    client = Mock()
    client.messages.create.return_value = response
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr("anthropic.Anthropic", lambda: client)
    prediction = categorizer.predict_one("ambiguous merchant", -11)
    assert prediction.category == "other"
    assert prediction.source == "llm"
    client.messages.create.assert_called_once()
