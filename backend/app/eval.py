"""Deterministic, offline evaluation harness for the FinScope pipeline."""

from __future__ import annotations

import argparse
import csv
import math
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from numbers import Real
from pathlib import Path
from typing import Any

import pandas as pd
import yaml  # type: ignore[import-untyped]  # PyYAML has no bundled type stubs.
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
from sqlalchemy import create_engine, text

from app import recurring as recurring_module
from app.anomaly import detect_anomalies
from app.categorize import (
    CONFIDENCE_THRESHOLD,
    TAXONOMY,
    Categorizer,
    _rule_match,
    categorize_many,
)
from app.etl import clean_merchant
from app.forecast import build_forecast
from app.nlq import GuardrailError, validate_sql
from app.recurring import RecurringGroup, detect_recurring
from app.recurring import Transaction as RecurringTransaction
from app.services.import_service import make_dedupe_key
from app.train_categorizer import train as train_categorizer

ROOT = Path(__file__).resolve().parents[2]
ANOMALY_TRUTH_PATH = ROOT / "backend" / "tests" / "fixtures" / "anomaly_truth.csv"
NLQ_FIXTURE_PATH = ROOT / "backend" / "tests" / "fixtures" / "nlq_cases.yaml"

GATES: dict[str, tuple[str, float]] = {
    "categorizer_accuracy": ("≥", 0.90),
    "categorizer_macro_f1": ("≥", 0.85),
    "recurring_precision": ("≥", 0.85),
    "recurring_recall": ("≥", 0.80),
    "anomaly_precision": ("≥", 0.70),
    "anomaly_false_alerts_per_100": ("≤", 1.0),
    "nlq_valid_sql_rate": ("≥", 0.95),
    "nlq_execution_accuracy": ("≥", 0.80),
}


@dataclass
class CategorizerAblation:
    name: str
    accuracy: float
    review_rate: float


@dataclass
class ThresholdResult:
    threshold: float
    accuracy: float
    review_rate: float


@dataclass
class RecurringAblation:
    name: str
    precision: float


@dataclass
class EvaluationResult:
    metrics: dict[str, float]
    per_class: dict[str, tuple[float, float]]
    confusion_labels: list[str]
    confusion: list[list[int]]
    categorizer_ablations: list[CategorizerAblation]
    threshold_sweep: list[ThresholdResult]
    recurring_ablations: list[RecurringAblation]


def _safe_divide(numerator: int | float, denominator: int | float) -> float:
    return float(numerator / denominator) if denominator else 0.0


def _is_true(value: object) -> bool:
    return str(value).strip().casefold() in {"1", "true", "yes"}


def _generate_synthetic(output_path: Path, seed: int, split: str) -> Path:
    """Run the repository generator so eval uses the same source as the demo."""
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "data" / "generate_synthetic.py"),
            "--months",
            "12",
            "--seed",
            str(seed),
            "--split",
            split,
            "--out",
            str(output_path),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return output_path.with_suffix(".labels.csv")


def _classification_metrics(
    expected: Sequence[str], predicted: Sequence[str], review_flags: Sequence[bool]
) -> tuple[dict[str, float], dict[str, tuple[float, float]], list[list[int]]]:
    precision, recall, f1, _support = precision_recall_fscore_support(
        expected,
        predicted,
        labels=TAXONOMY,
        zero_division=0,
    )
    per_class = {
        category: (float(precision[index]), float(recall[index]))
        for index, category in enumerate(TAXONOMY)
    }
    present_categories = set(expected) | set(predicted)
    metrics = {
        "categorizer_accuracy": _safe_divide(
            sum(actual == guess for actual, guess in zip(expected, predicted)),  # noqa: B905
            len(expected),
        ),
        "categorizer_macro_f1": _safe_divide(
            sum(
                float(f1[index])
                for index, category in enumerate(TAXONOMY)
                if category in present_categories
            ),
            len(present_categories),
        ),
        "categorizer_manual_review_rate": _safe_divide(sum(review_flags), len(review_flags)),
    }
    matrix = confusion_matrix(expected, predicted, labels=TAXONOMY).tolist()
    return metrics, per_class, matrix


def _local_model_predictions(
    categorizer: Categorizer, descriptions: Sequence[str]
) -> tuple[list[str], list[float]]:
    model = categorizer._load()
    cleaned = [clean_merchant(description) for description in descriptions]
    probabilities = model.predict_proba(cleaned)
    classifier = model.named_steps["classifier"]
    categories: list[str] = []
    confidences: list[float] = []
    for row in probabilities:
        index = int(row.argmax())
        categories.append(str(classifier.classes_[index]))
        confidences.append(float(row[index]))
    return categories, confidences


def _categorizer_evaluation(
    labels: pd.DataFrame, model_path: Path
) -> tuple[
    dict[str, float],
    dict[str, tuple[float, float]],
    list[list[int]],
    list[CategorizerAblation],
    list[ThresholdResult],
]:
    categorizer = Categorizer(model_path)
    descriptions = labels["description"].astype(str).tolist()
    amounts = labels["amount"].astype(float).tolist()
    expected = labels["category"].astype(str).tolist()
    predictions = categorize_many(descriptions, amounts, categorizer)
    predicted = [prediction.category for prediction in predictions]
    review_flags = [prediction.low_confidence for prediction in predictions]
    metrics, per_class, matrix = _classification_metrics(expected, predicted, review_flags)

    rules_only = [(_rule_match(description) or "other") for description in descriptions]
    model_categories, model_confidences = _local_model_predictions(categorizer, descriptions)
    ablations = [
        CategorizerAblation(
            "rules-only",
            _safe_divide(
                sum(actual == guess for actual, guess in zip(expected, rules_only)),  # noqa: B905
                len(expected),
            ),
            _safe_divide(sum(category == "other" for category in rules_only), len(rules_only)),
        ),
        CategorizerAblation(
            "local-model-only",
            _safe_divide(
                sum(
                    actual == guess
                    for actual, guess in zip(expected, model_categories)  # noqa: B905
                ),
                len(expected),
            ),
            _safe_divide(
                sum(confidence < CONFIDENCE_THRESHOLD for confidence in model_confidences),
                len(model_confidences),
            ),
        ),
    ]
    threshold_sweep = []
    for threshold in (round(0.20 + index * 0.10, 2) for index in range(7)):
        reviewed = [
            prediction.source == "model" and prediction.confidence < threshold
            for prediction in predictions
        ]
        routed = [index for index, is_reviewed in enumerate(reviewed) if not is_reviewed]
        threshold_sweep.append(
            ThresholdResult(
                threshold,
                _safe_divide(
                    sum(expected[index] == predicted[index] for index in routed),
                    len(routed),
                ),
                _safe_divide(sum(reviewed), len(reviewed)),
            )
        )
    return metrics, per_class, matrix, ablations, threshold_sweep


def _recurring_transactions(labels: pd.DataFrame) -> list[RecurringTransaction]:
    return [
        RecurringTransaction(
            clean_merchant(str(row["description"])),
            date.fromisoformat(str(row["date"])),
            float(row["amount"]),
            str(row["category"]),
        )
        for row in labels.to_dict("records")
    ]


def _recurring_groups(
    transactions: list[RecurringTransaction], amount_stability: bool
) -> list[RecurringGroup]:
    previous_limit = recurring_module.MAX_AMOUNT_CV
    if not amount_stability:
        recurring_module.MAX_AMOUNT_CV = math.inf
    try:
        return detect_recurring(transactions, today=date(2026, 8, 31))
    finally:
        recurring_module.MAX_AMOUNT_CV = previous_limit


def _recurring_metrics(
    labels: pd.DataFrame, transactions: list[RecurringTransaction]
) -> tuple[dict[str, float], list[RecurringAblation]]:
    groups = _recurring_groups(transactions, amount_stability=True)
    merchants = {group.merchant for group in groups}
    expected = [_is_true(value) for value in labels["recurring"].tolist()]
    predicted = [transaction.merchant in merchants for transaction in transactions]
    true_positive = sum(
        actual and guess for actual, guess in zip(expected, predicted)  # noqa: B905
    )
    false_positive = sum(
        not actual and guess for actual, guess in zip(expected, predicted)  # noqa: B905
    )
    false_negative = sum(
        actual and not guess for actual, guess in zip(expected, predicted)  # noqa: B905
    )
    metrics = {
        "recurring_precision": _safe_divide(true_positive, true_positive + false_positive),
        "recurring_recall": _safe_divide(true_positive, true_positive + false_negative),
        "recurring_f1": _safe_divide(
            2 * true_positive,
            2 * true_positive + false_positive + false_negative,
        ),
    }
    without_filter = _recurring_groups(transactions, amount_stability=False)
    without_merchants = {group.merchant for group in without_filter}
    without_predicted = [transaction.merchant in without_merchants for transaction in transactions]
    without_true_positive = sum(
        actual and guess
        for actual, guess in zip(expected, without_predicted)  # noqa: B905
    )
    without_false_positive = sum(
        not actual and guess
        for actual, guess in zip(expected, without_predicted)  # noqa: B905
    )
    ablations = [
        RecurringAblation(
            "with amount-stability filter",
            metrics["recurring_precision"],
        ),
        RecurringAblation(
            "without amount-stability filter",
            _safe_divide(
                without_true_positive,
                without_true_positive + without_false_positive,
            ),
        ),
    ]
    return metrics, ablations


def _anomaly_metrics(labels: pd.DataFrame) -> dict[str, float]:
    transactions: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in labels.to_dict("records"):
        if _is_true(row["recurring"]):
            continue
        merchant = clean_merchant(str(row["description"]))
        amount = Decimal(str(row["amount"]))
        txn_date = date.fromisoformat(str(row["date"]))
        key = make_dedupe_key(txn_date, merchant, amount)
        if key in seen:
            continue
        seen.add(key)
        transactions.append(
            {
                "key": key,
                "amount": float(amount),
                "category": str(row["category"]),
                "merchant": merchant,
            }
        )

    flags = detect_anomalies(
        [float(row["amount"]) for row in transactions],
        [str(row["category"]) for row in transactions],
        [str(row["merchant"]) for row in transactions],
    )
    predicted = {
        str(transactions[flag.index]["key"])
        for flag in flags
        if 0 <= flag.index < len(transactions)
    }
    with ANOMALY_TRUTH_PATH.open(newline="") as truth_file:
        truth = {
            row["dedupe_key"]
            for row in csv.DictReader(truth_file)
            if row["expected_anomaly"] == "1"
        }
    true_positive = len(predicted & truth)
    false_positive = len(predicted - truth)
    false_negative = len(truth - predicted)
    return {
        "anomaly_precision": _safe_divide(true_positive, len(predicted)),
        "anomaly_recall": _safe_divide(true_positive, true_positive + false_negative),
        "anomaly_false_alerts_per_100": _safe_divide(false_positive, len(transactions)) * 100,
    }


def _monthly_totals(labels: pd.DataFrame) -> tuple[dict[date, float], list[dict[str, Any]]]:
    totals: dict[date, float] = {}
    transactions: list[dict[str, Any]] = []
    for row in labels.to_dict("records"):
        txn_date = date.fromisoformat(str(row["date"]))
        amount = float(row["amount"])
        if amount >= 0:
            continue
        month = txn_date.replace(day=1)
        totals[month] = totals.get(month, 0.0) + amount
        transactions.append(
            {
                "txn_date": txn_date,
                "amount": amount,
                "category": str(row["category"]),
            }
        )
    return dict(sorted(totals.items())), transactions


def _forecast_mape(labels: pd.DataFrame) -> float:
    totals, transactions = _monthly_totals(labels)
    months = list(totals)
    errors: list[float] = []
    for target_month in months[-3:]:
        history = [
            transaction
            for transaction in transactions
            if transaction["txn_date"] < target_month
        ]
        forecast = build_forecast(history)
        actual = abs(totals[target_month])
        predicted = abs(forecast.total_spend.point)
        if actual:
            errors.append(abs(actual - predicted) / actual)
    build_forecast(transactions)
    return _safe_divide(sum(errors), len(errors)) * 100


NLQ_ROWS: tuple[tuple[str, str, float, str, bool], ...] = (
    ("2026-01-05", "STARBUCKS", -5, "coffee", False),
    ("2026-01-10", "WHOLE FOODS", -20, "groceries", False),
    ("2026-02-05", "STARBUCKS", -6, "coffee", False),
    ("2026-02-10", "NETFLIX", -16, "subscriptions", True),
    ("2026-03-05", "STARBUCKS", -7, "coffee", False),
    ("2026-03-10", "RENT", -1000, "rent_mortgage", True),
    ("2026-04-10", "WHOLE FOODS", -25, "groceries", False),
    ("2026-05-05", "STARBUCKS", -8, "coffee", False),
    ("2026-06-10", "TARGET", -50, "shopping", False),
    ("2026-06-15", "SALARY", 3000, "income", False),
    ("2026-07-10", "NETFLIX", -18, "subscriptions", True),
    ("2026-08-05", "STARBUCKS", -9, "coffee", False),
    ("2026-08-15", "SALARY", 3000, "income", False),
)


def _rows_equal(actual: list[dict[str, Any]], expected: object) -> bool:
    if not isinstance(expected, list) or len(actual) != len(expected):
        return False
    for actual_row, expected_row in zip(actual, expected):  # noqa: B905
        if not isinstance(expected_row, Mapping) or set(actual_row) != set(expected_row):
            return False
        for key, actual_value in actual_row.items():
            expected_value = expected_row[key]
            if isinstance(actual_value, Real) and isinstance(expected_value, Real):
                if not math.isclose(float(actual_value), float(expected_value), rel_tol=1e-9):
                    return False
            elif str(actual_value) != str(expected_value):
                return False
    return True


def _nlq_metrics() -> dict[str, float]:
    cases = yaml.safe_load(NLQ_FIXTURE_PATH.read_text(encoding="utf-8"))
    engine = create_engine("sqlite://")
    valid = 0
    executed_correctly = 0
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE transactions ("
                    "txn_date TEXT, merchant TEXT, amount REAL, category TEXT, "
                    "is_recurring BOOLEAN)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO transactions "
                    "(txn_date, merchant, amount, category, is_recurring) "
                    "VALUES (:txn_date, :merchant, :amount, :category, :is_recurring)"
                ),
                [
                    {
                        "txn_date": txn_date,
                        "merchant": merchant,
                        "amount": amount,
                        "category": category,
                        "is_recurring": recurring,
                    }
                    for txn_date, merchant, amount, category, recurring in NLQ_ROWS
                ],
            )
            connection.execute(
                text(
                    "CREATE VIEW v_readonly_transactions AS "
                    "SELECT txn_date, merchant, amount, category, is_recurring "
                    "FROM transactions"
                )
            )
            for case in cases:
                try:
                    safe_sql = validate_sql(str(case["gold_sql"]))
                except GuardrailError:
                    continue
                valid += 1
                try:
                    result = connection.execute(text(safe_sql))
                    rows = [dict(row._mapping) for row in result]
                except Exception:  # noqa: BLE001
                    continue
                if _rows_equal(rows, case.get("gold_result")):
                    executed_correctly += 1
    finally:
        engine.dispose()
    total = len(cases)
    return {
        "nlq_valid_sql_rate": _safe_divide(valid, total),
        "nlq_execution_accuracy": _safe_divide(executed_correctly, total),
    }


def run_evaluation() -> EvaluationResult:
    """Run every offline evaluation and return report-ready values."""
    with tempfile.TemporaryDirectory(prefix="finscope-eval-") as temporary_directory:
        temporary_path = Path(temporary_directory)
        train_statement_path = temporary_path / "train_statement.csv"
        eval_statement_path = temporary_path / "eval_statement.csv"
        train_labels_path = _generate_synthetic(train_statement_path, seed=42, split="train")
        eval_labels_path = _generate_synthetic(eval_statement_path, seed=7, split="eval")
        eval_labels = pd.read_csv(eval_labels_path)
        model_path = temporary_path / "categorizer.joblib"
        train_categorizer(train_labels_path, model_path, database_url=None)

        (
            categorizer_metrics,
            per_class,
            matrix,
            categorizer_ablations,
            threshold_sweep,
        ) = _categorizer_evaluation(eval_labels, model_path)
        transactions = _recurring_transactions(eval_labels)
        recurring_metrics, recurring_ablations = _recurring_metrics(eval_labels, transactions)
        metrics = {
            **categorizer_metrics,
            **recurring_metrics,
            **_anomaly_metrics(eval_labels),
            "forecaster_mape": _forecast_mape(eval_labels),
            **_nlq_metrics(),
        }
        return EvaluationResult(
            metrics=metrics,
            per_class=per_class,
            confusion_labels=list(TAXONOMY),
            confusion=matrix,
            categorizer_ablations=categorizer_ablations,
            threshold_sweep=threshold_sweep,
            recurring_ablations=recurring_ablations,
        )


def _gate_status(metric: str, value: float) -> tuple[str, str]:
    if metric not in GATES:
        return "reported", "REPORTED"
    operator, threshold = GATES[metric]
    passed = value >= threshold if operator == "≥" else value <= threshold
    return f"{operator} {threshold:g}", "PASS" if passed else "FAIL"


def _failed_gates(metrics: Mapping[str, float]) -> list[str]:
    failures: list[str] = []
    for metric, (operator, threshold) in GATES.items():
        value = metrics[metric]
        passed = value >= threshold if operator == "≥" else value <= threshold
        if not passed:
            failures.append(f"{metric}={value:.4f} (gate {operator} {threshold:g})")
    return failures


SUMMARY_ROWS: tuple[tuple[str, str, str], ...] = (
    ("Categorizer", "accuracy", "categorizer_accuracy"),
    ("Categorizer", "macro-F1", "categorizer_macro_f1"),
    ("Categorizer", "manual-review rate", "categorizer_manual_review_rate"),
    ("Recurring detector", "precision", "recurring_precision"),
    ("Recurring detector", "recall", "recurring_recall"),
    ("Recurring detector", "F1", "recurring_f1"),
    ("Anomaly detector", "precision", "anomaly_precision"),
    ("Anomaly detector", "recall", "anomaly_recall"),
    ("Anomaly detector", "false alerts / 100 txns", "anomaly_false_alerts_per_100"),
    ("Forecaster", "MAPE (3-month backtest)", "forecaster_mape"),
    ("NL→SQL", "valid-SQL rate", "nlq_valid_sql_rate"),
    ("NL→SQL", "execution accuracy", "nlq_execution_accuracy"),
)


def write_report(result: EvaluationResult, report_path: Path) -> None:
    """Write the complete evaluation result as Markdown."""
    lines = [
        "# FinScope Evaluation Report",
        "",
        f"Generated on: {date.today().isoformat()}",
        "",
        "Synthetic data: 12 months; categorizer train split (seed 42) and eval "
        "split (seed 7). All metrics are computed offline.",
        "",
        "## Summary",
        "",
        "| Component | Metric | Value | Gate | Status |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for component, label, metric in SUMMARY_ROWS:
        gate, status = _gate_status(metric, result.metrics[metric])
        lines.append(
            f"| {component} | {label} | {result.metrics[metric]:.4f} | {gate} | {status} |"
        )
    for category, (precision, recall) in result.per_class.items():
        lines.append(
            f"| Categorizer | {category} precision | {precision:.4f} | reported | REPORTED |"
        )
        lines.append(
            f"| Categorizer | {category} recall | {recall:.4f} | reported | REPORTED |"
        )

    lines.extend(
        [
            "",
            "## Categorizer confusion matrix",
            "",
            "| Actual \\ Predicted | " + " | ".join(result.confusion_labels) + " |",
            "| --- | " + " | ".join("---:" for _ in result.confusion_labels) + " |",
        ]
    )
    for label, row in zip(result.confusion_labels, result.confusion):  # noqa: B905
        lines.append(f"| {label} | " + " | ".join(str(value) for value in row) + " |")

    lines.extend(["", "## Ablations", "", "### Categorizer routing", ""])
    lines.extend(
        [
            "| Configuration | Accuracy | Review rate |",
            "| --- | ---: | ---: |",
        ]
    )
    lines.extend(
        f"| {row.name} | {row.accuracy:.4f} | {row.review_rate:.4f} |"
        for row in result.categorizer_ablations
    )
    lines.extend(["", "### Confidence threshold sweep", ""])
    lines.extend(
        [
            "| Threshold | Auto-routed accuracy | Review rate |",
            "| ---: | ---: | ---: |",
        ]
    )
    lines.extend(
        f"| {row.threshold:.2f} | {row.accuracy:.4f} | {row.review_rate:.4f} |"
        for row in result.threshold_sweep
    )
    lines.extend(["", "### Recurring amount-stability filter", ""])
    lines.extend(
        [
            "| Configuration | Precision |",
            "| --- | ---: |",
        ]
    )
    lines.extend(f"| {row.name} | {row.precision:.4f} |" for row in result.recurring_ablations)
    lines.extend(
        [
            "",
            "## Evaluation notes",
            "",
            "- Categorization trains on the first half of each merchant's variants (seed 42) "
            "and evaluates on the second half (seed 7), including rare long-tail and "
            "ambiguous transactions.",
            "- Recurring detection is evaluated against the labels' recurring flag.",
            "- Anomaly detection excludes labeled recurring transactions and exact duplicates, "
            "matching the import pipeline and anomaly fixture tests.",
            "- NL→SQL uses each fixture's `gold_sql` as the generated SQL; no Anthropic API "
            "call is made.",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the offline FinScope evaluation harness")
    parser.add_argument("--report", type=Path, required=True, help="Markdown report output path")
    args = parser.parse_args(argv)
    result = run_evaluation()
    write_report(result, args.report)
    failures = _failed_gates(result.metrics)
    if failures:
        print("Evaluation gates: FAIL — " + "; ".join(failures))
        return 1
    print("Evaluation gates: PASS — all gated metrics met")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
