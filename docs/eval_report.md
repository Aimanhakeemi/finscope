# FinScope Evaluation Report

Generated on: 2026-08-31

Synthetic data: 12 months, seed 42. All metrics are computed offline.

## Summary

| Component | Metric | Value | Gate | Status |
| --- | --- | ---: | ---: | --- |
| Categorizer | accuracy | 1.0000 | ≥ 0.9 | PASS |
| Categorizer | macro-F1 | 1.0000 | ≥ 0.85 | PASS |
| Categorizer | manual-review rate | 0.0019 | reported | REPORTED |
| Recurring detector | precision | 1.0000 | ≥ 0.85 | PASS |
| Recurring detector | recall | 1.0000 | ≥ 0.8 | PASS |
| Recurring detector | F1 | 1.0000 | reported | REPORTED |
| Anomaly detector | precision | 1.0000 | ≥ 0.7 | PASS |
| Anomaly detector | recall | 1.0000 | reported | REPORTED |
| Anomaly detector | false alerts / 100 txns | 0.0000 | ≤ 1 | PASS |
| Forecaster | MAPE (3-month backtest) | 30.9424 | reported | REPORTED |
| NL→SQL | valid-SQL rate | 1.0000 | ≥ 0.95 | PASS |
| NL→SQL | execution accuracy | 1.0000 | ≥ 0.8 | PASS |
| Categorizer | groceries precision | 1.0000 | reported | REPORTED |
| Categorizer | groceries recall | 1.0000 | reported | REPORTED |
| Categorizer | dining precision | 1.0000 | reported | REPORTED |
| Categorizer | dining recall | 1.0000 | reported | REPORTED |
| Categorizer | coffee precision | 1.0000 | reported | REPORTED |
| Categorizer | coffee recall | 1.0000 | reported | REPORTED |
| Categorizer | transport precision | 1.0000 | reported | REPORTED |
| Categorizer | transport recall | 1.0000 | reported | REPORTED |
| Categorizer | fuel precision | 1.0000 | reported | REPORTED |
| Categorizer | fuel recall | 1.0000 | reported | REPORTED |
| Categorizer | utilities precision | 1.0000 | reported | REPORTED |
| Categorizer | utilities recall | 1.0000 | reported | REPORTED |
| Categorizer | rent_mortgage precision | 1.0000 | reported | REPORTED |
| Categorizer | rent_mortgage recall | 1.0000 | reported | REPORTED |
| Categorizer | subscriptions precision | 1.0000 | reported | REPORTED |
| Categorizer | subscriptions recall | 1.0000 | reported | REPORTED |
| Categorizer | shopping precision | 1.0000 | reported | REPORTED |
| Categorizer | shopping recall | 1.0000 | reported | REPORTED |
| Categorizer | health precision | 1.0000 | reported | REPORTED |
| Categorizer | health recall | 1.0000 | reported | REPORTED |
| Categorizer | entertainment precision | 0.0000 | reported | REPORTED |
| Categorizer | entertainment recall | 0.0000 | reported | REPORTED |
| Categorizer | income precision | 1.0000 | reported | REPORTED |
| Categorizer | income recall | 1.0000 | reported | REPORTED |
| Categorizer | other precision | 1.0000 | reported | REPORTED |
| Categorizer | other recall | 1.0000 | reported | REPORTED |

## Categorizer confusion matrix

| Actual \ Predicted | groceries | dining | coffee | transport | fuel | utilities | rent_mortgage | subscriptions | shopping | health | entertainment | income | other |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| groceries | 52 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| dining | 0 | 29 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| coffee | 0 | 0 | 187 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| transport | 0 | 0 | 0 | 24 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| fuel | 0 | 0 | 0 | 0 | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| utilities | 0 | 0 | 0 | 0 | 0 | 24 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| rent_mortgage | 0 | 0 | 0 | 0 | 0 | 0 | 13 | 0 | 0 | 0 | 0 | 0 | 0 |
| subscriptions | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 88 | 0 | 0 | 0 | 0 | 0 |
| shopping | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 31 | 0 | 0 | 0 | 0 |
| health | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 23 | 0 | 0 | 0 |
| entertainment | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| income | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 26 | 0 |
| other | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |

## Ablations

### Categorizer routing

| Configuration | Accuracy | Review rate |
| --- | ---: | ---: |
| rules-only | 0.8842 | 0.1178 |
| local-model-only | 1.0000 | 0.0019 |

### Confidence threshold sweep

| Threshold | Accuracy | Review rate |
| ---: | ---: | ---: |
| 0.40 | 1.0000 | 0.0019 |
| 0.45 | 1.0000 | 0.0019 |
| 0.50 | 1.0000 | 0.0019 |
| 0.55 | 1.0000 | 0.0019 |
| 0.60 | 1.0000 | 0.0019 |
| 0.65 | 1.0000 | 0.0019 |
| 0.70 | 1.0000 | 0.0019 |

### Recurring amount-stability filter

| Configuration | Precision |
| --- | ---: |
| with amount-stability filter | 1.0000 |
| without amount-stability filter | 0.9368 |

## Evaluation notes

- Categorization trains on the generated labels and evaluates every generated row.
- Recurring detection is evaluated against the labels' recurring flag.
- Anomaly detection excludes labeled recurring transactions and exact duplicates, matching the import pipeline and anomaly fixture tests.
- NL→SQL uses each fixture's `gold_sql` as the generated SQL; no Anthropic API call is made.
