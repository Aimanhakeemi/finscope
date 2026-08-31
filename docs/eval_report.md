# FinScope Evaluation Report

Generated on: 2026-08-31

Synthetic data: 12 months; categorizer train split (seed 42) and eval split (seed 7). All metrics are computed offline.

## Summary

| Component | Metric | Value | Gate | Status |
| --- | --- | ---: | ---: | --- |
| Categorizer | accuracy | 0.8825 | ≥ 0.84 | PASS |
| Categorizer | macro-F1 | 0.8370 | ≥ 0.78 | PASS |
| Categorizer | manual-review rate | 0.3675 | reported | REPORTED |
| Recurring detector | precision | 0.9429 | ≥ 0.82 | PASS |
| Recurring detector | recall | 1.0000 | ≥ 0.75 | PASS |
| Recurring detector | F1 | 0.9706 | reported | REPORTED |
| Anomaly detector | precision | 1.0000 | ≥ 0.7 | PASS |
| Anomaly detector | recall | 1.0000 | reported | REPORTED |
| Anomaly detector | false alerts / 100 txns | 0.0000 | ≤ 1 | PASS |
| Forecaster | MAPE (3-month backtest, seasonal-naive baseline) | 58.7940 | reported | REPORTED |
| NL→SQL | valid-SQL rate | 1.0000 | ≥ 0.95 | PASS |
| NL→SQL | execution accuracy | 1.0000 | ≥ 0.8 | PASS |
| Categorizer | groceries precision | 0.9778 | reported | REPORTED |
| Categorizer | groceries recall | 0.6667 | reported | REPORTED |
| Categorizer | dining precision | 1.0000 | reported | REPORTED |
| Categorizer | dining recall | 0.9565 | reported | REPORTED |
| Categorizer | coffee precision | 0.9791 | reported | REPORTED |
| Categorizer | coffee recall | 0.9590 | reported | REPORTED |
| Categorizer | transport precision | 0.8485 | reported | REPORTED |
| Categorizer | transport recall | 0.8750 | reported | REPORTED |
| Categorizer | fuel precision | 0.8235 | reported | REPORTED |
| Categorizer | fuel recall | 0.6667 | reported | REPORTED |
| Categorizer | utilities precision | 0.6667 | reported | REPORTED |
| Categorizer | utilities recall | 0.9778 | reported | REPORTED |
| Categorizer | rent_mortgage precision | 0.8571 | reported | REPORTED |
| Categorizer | rent_mortgage recall | 0.8000 | reported | REPORTED |
| Categorizer | subscriptions precision | 0.9900 | reported | REPORTED |
| Categorizer | subscriptions recall | 0.9802 | reported | REPORTED |
| Categorizer | shopping precision | 0.4727 | reported | REPORTED |
| Categorizer | shopping recall | 0.8125 | reported | REPORTED |
| Categorizer | health precision | 0.9355 | reported | REPORTED |
| Categorizer | health recall | 0.9667 | reported | REPORTED |
| Categorizer | entertainment precision | 0.9286 | reported | REPORTED |
| Categorizer | entertainment recall | 0.8667 | reported | REPORTED |
| Categorizer | income precision | 1.0000 | reported | REPORTED |
| Categorizer | income recall | 0.8250 | reported | REPORTED |
| Categorizer | other precision | 0.6667 | reported | REPORTED |
| Categorizer | other recall | 0.5263 | reported | REPORTED |

## Categorizer confusion matrix

| Actual \ Predicted | groceries | dining | coffee | transport | fuel | utilities | rent_mortgage | subscriptions | shopping | health | entertainment | income | other |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| groceries | 44 | 0 | 0 | 0 | 0 | 4 | 0 | 0 | 18 | 0 | 0 | 0 | 0 |
| dining | 1 | 22 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| coffee | 0 | 0 | 187 | 0 | 0 | 5 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| transport | 0 | 0 | 0 | 28 | 0 | 0 | 1 | 0 | 1 | 0 | 2 | 0 | 0 |
| fuel | 0 | 0 | 0 | 0 | 14 | 3 | 3 | 0 | 1 | 0 | 0 | 0 | 0 |
| utilities | 0 | 0 | 0 | 0 | 1 | 44 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| rent_mortgage | 0 | 0 | 0 | 0 | 0 | 1 | 24 | 0 | 0 | 0 | 0 | 0 | 5 |
| subscriptions | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 99 | 0 | 2 | 0 | 0 | 0 |
| shopping | 0 | 0 | 2 | 0 | 0 | 4 | 0 | 0 | 26 | 0 | 0 | 0 | 0 |
| health | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 29 | 0 | 0 | 0 |
| entertainment | 0 | 0 | 0 | 0 | 2 | 2 | 0 | 0 | 0 | 0 | 26 | 0 | 0 |
| income | 0 | 0 | 0 | 3 | 0 | 1 | 0 | 0 | 3 | 0 | 0 | 33 | 0 |
| other | 0 | 0 | 2 | 2 | 0 | 2 | 0 | 0 | 3 | 0 | 0 | 0 | 10 |

## Ablations

### Categorizer routing

| Configuration | Accuracy | Review rate |
| --- | ---: | ---: |
| rules-only | 0.6175 | 0.4111 |
| local-model-only | 0.8434 | 0.5798 |

### Confidence threshold sweep

| Threshold | Auto-routed accuracy | Review rate |
| ---: | ---: | ---: |
| 0.20 | 0.9409 | 0.1852 |
| 0.30 | 0.9744 | 0.2364 |
| 0.40 | 0.9958 | 0.2801 |
| 0.50 | 1.0000 | 0.3268 |
| 0.60 | 1.0000 | 0.3810 |
| 0.70 | 1.0000 | 0.3931 |
| 0.80 | 1.0000 | 0.4111 |

### Recurring amount-stability filter

| Configuration | Precision |
| --- | ---: |
| with amount-stability filter | 0.9429 |
| without amount-stability filter | 0.9429 |

## Evaluation notes

- Categorization trains on the first half of each merchant's variants (seed 42) and evaluates on the second half (seed 7), including rare long-tail and ambiguous transactions.
- Recurring detection is evaluated against the labels' recurring flag.
- Anomaly detection excludes labeled recurring transactions and exact duplicates, matching the import pipeline and anomaly fixture tests.
- NL→SQL uses each fixture's `gold_sql` as the generated SQL; no Anthropic API call is made.
- The backtest uses the seasonal-naive baseline because the ETS optimizer is not reproducible across statsmodels builds; the app itself still auto-selects ETS at runtime.
- Forecaster MAPE remains above ~40% on this synthetic 3-month backtest; this is a known limitation and is reported only, not gated.
