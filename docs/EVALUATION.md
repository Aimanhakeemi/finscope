# FinScope — Evaluation

The evaluation harness is a first-class part of the project: it is what makes this
an *AI engineering* portfolio piece rather than a demo.

## How it runs

```bash
cd backend && python -m app.eval --report ../docs/eval_report.md
```

Steps:
1. Generate a fresh synthetic statement + labels with a fixed seed.
2. Run the full pipeline (ETL → categorize → recurring → anomaly → forecast).
3. Compare against `data/sample_statement.labels.csv` and the NL→SQL fixture.
4. Write a Markdown report with tables + a confusion matrix, and exit non-zero if
   any gated metric regresses below its threshold (so CI catches it).

## Fixtures

| File | Purpose |
| --- | --- |
| `data/sample_statement.csv` | pipeline input |
| `data/sample_statement.labels.csv` | true category + recurring flag per row |
| `backend/tests/fixtures/nlq_cases.yaml` | 25 question → gold-SQL / gold-result pairs |
| `backend/tests/fixtures/anomaly_truth.csv` | ids of injected anomalies |

## Metrics & gates

| Component | Metric | Gate |
| --- | --- | --- |
| Categorizer | accuracy | ≥ 0.90 |
| Categorizer | macro-F1 | ≥ 0.85 |
| Categorizer | LLM-call rate | reported (target ≤ 0.15) |
| Recurring detector | precision | ≥ 0.85 |
| Recurring detector | recall | ≥ 0.80 |
| Anomaly detector | precision | ≥ 0.70 |
| Anomaly detector | false alerts / 100 txns | ≤ 1.0 |
| Forecaster | MAPE (3-month backtest) | reported only |
| NL→SQL | valid-SQL rate | ≥ 0.95 |
| NL→SQL | execution accuracy | ≥ 0.80 |

## Ablations worth showing in the report

- Categorizer: rules-only vs. model-only vs. model+LLM router — accuracy and cost.
- Confidence threshold sweep (0.4 → 0.7) → accuracy vs. LLM-call rate curve.
- Recurring detector: effect of the amount-stability filter on precision.

## CI integration

`.github/workflows/ci.yml` runs `python -m app.eval` on every push. A regression
below a gate fails the build. The committed `docs/eval_report.md` is regenerated
and diffed so reviewers can see metric movement per PR.
