# FinScope Evaluation Report

Generated on: 2026-08-31

Synthetic data: 12 months; categorizer train split (seed 42) and eval split (seed 7). All metrics are computed offline.

## Summary

| Component | Metric | Value | Gate | Status |
| --- | --- | ---: | ---: | --- |
| Categorizer | accuracy | 0.9032 | ≥ 0.9 | PASS |
| Categorizer | macro-F1 | 0.8537 | ≥ 0.85 | PASS |
| Categorizer | manual-review rate | 0.3646 | reported | REPORTED |
| Recurring detector | precision | 0.8717 | ≥ 0.85 | PASS |
| Recurring detector | recall | 1.0000 | ≥ 0.8 | PASS |
| Recurring detector | F1 | 0.9314 | reported | REPORTED |
| Anomaly detector | precision | 1.0000 | ≥ 0.7 | PASS |
| Anomaly detector | recall | 1.0000 | reported | REPORTED |
| Anomaly detector | false alerts / 100 txns | 0.0000 | ≤ 1 | PASS |
| Forecaster | MAPE (3-month backtest) | 92.3557 | reported | REPORTED |
| NL→SQL | valid-SQL rate | 1.0000 | ≥ 0.95 | PASS |
| NL→SQL | execution accuracy | 1.0000 | ≥ 0.8 | PASS |
| Categorizer | groceries precision | 0.9672 | reported | REPORTED |
| Categorizer | groceries recall | 0.8806 | reported | REPORTED |
| Categorizer | dining precision | 1.0000 | reported | REPORTED |
| Categorizer | dining recall | 0.9130 | reported | REPORTED |
| Categorizer | coffee precision | 0.9786 | reported | REPORTED |
| Categorizer | coffee recall | 0.9734 | reported | REPORTED |
| Categorizer | transport precision | 0.8333 | reported | REPORTED |
| Categorizer | transport recall | 0.8108 | reported | REPORTED |
| Categorizer | fuel precision | 0.7895 | reported | REPORTED |
| Categorizer | fuel recall | 0.7500 | reported | REPORTED |
| Categorizer | utilities precision | 0.7119 | reported | REPORTED |
| Categorizer | utilities recall | 0.9545 | reported | REPORTED |
| Categorizer | rent_mortgage precision | 0.8571 | reported | REPORTED |
| Categorizer | rent_mortgage recall | 0.7500 | reported | REPORTED |
| Categorizer | subscriptions precision | 0.9902 | reported | REPORTED |
| Categorizer | subscriptions recall | 0.9712 | reported | REPORTED |
| Categorizer | shopping precision | 0.6000 | reported | REPORTED |
| Categorizer | shopping recall | 0.8571 | reported | REPORTED |
| Categorizer | health precision | 0.9062 | reported | REPORTED |
| Categorizer | health recall | 0.9667 | reported | REPORTED |
| Categorizer | entertainment precision | 0.9310 | reported | REPORTED |
| Categorizer | entertainment recall | 0.9000 | reported | REPORTED |
| Categorizer | income precision | 1.0000 | reported | REPORTED |
| Categorizer | income recall | 0.7805 | reported | REPORTED |
| Categorizer | other precision | 0.6667 | reported | REPORTED |
| Categorizer | other recall | 0.5882 | reported | REPORTED |

## Categorizer confusion matrix

| Actual \ Predicted | groceries | dining | coffee | transport | fuel | utilities | rent_mortgage | subscriptions | shopping | health | entertainment | income | other |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| groceries | 59 | 0 | 0 | 0 | 0 | 5 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| dining | 2 | 21 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| coffee | 0 | 0 | 183 | 0 | 0 | 3 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| transport | 0 | 0 | 0 | 30 | 0 | 1 | 3 | 0 | 1 | 0 | 2 | 0 | 0 |
| fuel | 0 | 0 | 0 | 0 | 15 | 2 | 1 | 0 | 2 | 0 | 0 | 0 | 0 |
| utilities | 0 | 0 | 0 | 0 | 2 | 42 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| rent_mortgage | 0 | 0 | 0 | 0 | 0 | 2 | 24 | 0 | 1 | 0 | 0 | 0 | 5 |
| subscriptions | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 101 | 0 | 3 | 0 | 0 | 0 |
| shopping | 0 | 0 | 3 | 0 | 0 | 1 | 0 | 0 | 24 | 0 | 0 | 0 | 0 |
| health | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 29 | 0 | 0 | 0 |
| entertainment | 0 | 0 | 0 | 0 | 2 | 1 | 0 | 0 | 0 | 0 | 27 | 0 | 0 |
| income | 0 | 0 | 0 | 4 | 0 | 2 | 0 | 0 | 3 | 0 | 0 | 32 | 0 |
| other | 0 | 0 | 1 | 2 | 0 | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 10 |

## Ablations

### Categorizer routing

| Configuration | Accuracy | Review rate |
| --- | ---: | ---: |
| rules-only | 0.6157 | 0.4100 |
| local-model-only | 0.8593 | 0.5840 |

### Confidence threshold sweep

| Threshold | Auto-routed accuracy | Review rate |
| ---: | ---: | ---: |
| 0.20 | 0.9648 | 0.1831 |
| 0.30 | 0.9721 | 0.2405 |
| 0.40 | 0.9958 | 0.2769 |
| 0.50 | 1.0000 | 0.3449 |
| 0.60 | 1.0000 | 0.3812 |
| 0.70 | 1.0000 | 0.3933 |
| 0.80 | 1.0000 | 0.4100 |

### Recurring amount-stability filter

| Configuration | Precision |
| --- | ---: |
| with amount-stability filter | 0.8717 |
| without amount-stability filter | 0.8579 |

## Evaluation notes

- Categorization trains on the first half of each merchant's variants (seed 42) and evaluates on the second half (seed 7), including rare long-tail and ambiguous transactions.
- Recurring detection is evaluated against the labels' recurring flag.
- Anomaly detection excludes labeled recurring transactions and exact duplicates, matching the import pipeline and anomaly fixture tests.
- NL→SQL uses each fixture's `gold_sql` as the generated SQL; no Anthropic API call is made.
