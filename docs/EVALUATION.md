# FinScope — Evaluation

The evaluation harness is a first-class part of the project: it is what makes this
an *AI engineering* portfolio piece rather than a demo.

## How it runs

```bash
cd backend && python -m app.eval --report ../docs/eval_report.md
```

Steps:
1. Generate a fresh synthetic train split (seed 42) and eval split (seed 7). The
   categorizer trains on the train labels, then scores only the eval labels. The eval
   split contains unseen variant forms, rare long-tail merchants, and ambiguous rows.
2. Run the full pipeline (ETL → categorize → recurring → anomaly → forecast) on the
   eval split.
3. Compare against the eval labels and the NL→SQL fixture.
4. Write a Markdown report with tables + a confusion matrix, and exit non-zero if
   any gated metric regresses below its threshold (so CI catches it).

## Fixtures

| File | Purpose |
| --- | --- |
| `data/sample_statement.csv` | pipeline input |
| `data/sample_statement.labels.csv` | true category + recurring flag per row |
| `data/generate_synthetic.py --split train` | first-half variants, no long-tail rows |
| `data/generate_synthetic.py --split eval` | second-half variants, long-tail + ambiguous rows |
| `backend/tests/fixtures/nlq_cases.yaml` | 25 question → gold-SQL / gold-result pairs |
| `backend/tests/fixtures/anomaly_truth.csv` | ids of injected anomalies |

## Metrics & gates

| Component | Metric | Gate |
| --- | --- | --- |
| Categorizer | accuracy | ≥ 0.84 |
| Categorizer | macro-F1 | ≥ 0.78 |
| Categorizer | manual-review rate | reported |
| Recurring detector | precision | ≥ 0.82 |
| Recurring detector | recall | ≥ 0.75 |
| Anomaly detector | precision | ≥ 0.70 |
| Anomaly detector | false alerts / 100 txns | ≤ 1.0 |
| Forecaster | MAPE (3-month backtest, seasonal-naive baseline) | reported only |
| NL→SQL | valid-SQL rate | ≥ 0.95 |
| NL→SQL | execution accuracy | ≥ 0.80 |

The categorizer and recurring gates leave several points of headroom for normal CI float variance.

The backtest uses the seasonal-naive baseline because the ETS optimizer is not reproducible across statsmodels builds; the app itself still auto-selects ETS at runtime.

## Ablations worth showing in the report

- Categorizer: rules-only vs. local-model-only — accuracy and review rate.
- Confidence threshold sweep (0.2 → 0.8) → auto-routed accuracy vs. manual-review rate curve.
- Recurring detector: effect of the amount-stability filter on precision.

## CI integration

`.github/workflows/ci.yml` runs `python -m app.eval` on every push. A regression
below a gate fails the build. The committed `docs/eval_report.md` is regenerated
and diffed so reviewers can see metric movement per PR.
