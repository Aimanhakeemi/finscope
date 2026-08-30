from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from app.train_categorizer import train


def test_train_writes_model_and_sidecar(tmp_path: Path):
    labels = tmp_path / "labels.csv"
    pd.DataFrame(
        {
            "description": ["MARKET", "RESTAURANT", "GROCERY STORE", "DINER"],
            "category": ["groceries", "dining", "groceries", "dining"],
        }
    ).to_csv(labels, index=False)
    output = train(labels, tmp_path / "model.joblib")

    assert output.exists()
    sidecar = json.loads(output.with_suffix(".json").read_text())
    assert sidecar["rows"] == 4
    assert sidecar["classes"] == ["dining", "groceries"]
