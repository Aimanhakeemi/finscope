# FinScope — Model Card & AI Design

## 1. Transaction categorizer

### Task
Multi-class classification: transaction description → one of 12 categories.

### Data
- Training: synthetic labeled statement(s) + accumulated `category_corrections`.
- Realistically ~2–5k rows. Small, so a linear model beats anything heavy.

### Features
- `TfidfVectorizer(analyzer="char_wb", ngram_range=(2,4))` on the cleaned merchant
  string — robust to store numbers, spacing, abbreviations.
- Optional numeric side features: `amount` bucket, `is_round_number`, `weekday`.

### Model
- `LogisticRegression(max_iter=1000, class_weight="balanced")` (calibrated
  probabilities via `predict_proba`).
- Persisted to `backend/app/artifacts/categorizer.joblib`; version + training date
  recorded in a sidecar JSON.

### Confidence and manual review

```
p = model.predict_proba(x).max()
if merchant matches a rule        -> category = rule,  source = "rule",  conf = 1.0
else                              -> category = model best guess, source = "model", conf = p
```

The `0.55` `CONFIDENCE_THRESHOLD` is a review threshold, not a routing decision.
Rows with `confidence < 0.55` remain model predictions and set
`low_confidence = true` so the UI can surface them for manual review. User
corrections are persisted as training labels for the next local model retrain.

### LLM boundary

Categorization is rules plus a local scikit-learn model only. It never calls Claude.
Claude is reserved for the natural-language query feature, where its use is
auditable and limited to generating a read-only SQL query.

### Metrics
Accuracy, macro-F1, per-class precision/recall, confusion matrix, manual-review rate.
Targets: accuracy ≥ 0.90, macro-F1 ≥ 0.85.

### Known limitations
- Cold start on a brand-new user before any corrections.
- Ambiguous merchants (a supermarket that also sells fuel) — accepted error.
- Synthetic training data will not capture every real-world merchant string.

## 2. Recurring-payment detector (rule-based, not ML)

### Method
1. Group transactions by `merchant`.
2. For groups with ≥ 3 occurrences, sort by date, compute day-gaps.
3. Match the median gap to a cadence with tolerance:
   weekly 7±2, biweekly 14±3, monthly 30±5, quarterly 91±10, annual 365±20.
4. Require amount stability: `stddev / mean ≤ 0.25` (allows small price changes).
5. Emit a `recurring_group` with `next_expected = last_seen + cadence`.
- Detection is restricted to bill-like categories: `subscriptions`, `utilities`,
  `rent_mortgage`, `health`, `income`, `entertainment`, and `other`; variable
  consumer spending such as fuel, groceries, dining, coffee, transport, and
  shopping is not treated as a bill even when its timing and amounts look regular.

### Metrics
Precision / recall / F1 against the `recurring` flags in the labels file.
Targets: precision ≥ 0.85, recall ≥ 0.80.

## 3. Anomaly detector

### Method (per category)
- Robust z-score: `0.6745 * (x - median) / MAD`; flag `|z| > 3.5`.
- IQR fence: flag outside `[Q1 - 1.5·IQR, Q3 + 1.5·IQR]`.
- "New large merchant": first-ever charge for a merchant AND amount > 90th
  percentile of all outflows.
- A transaction is anomalous if ≥ 2 signals fire (keeps false positives low).

### Metrics
Precision / recall against the injected anomalies; false-alert rate per 100 txns.

## 4. Forecaster

### Method
- If ≥ 6 monthly points: `statsmodels` ETS (additive trend, no seasonality for
  total; seasonal-naive per category).
- Else: trailing 3-month median.
- 80% prediction interval from the model, or ±1.5·MAD for the fallback.

### Metrics
Backtest MAPE on the last 3 held-out months. Report, don't gate.

## 5. Natural-language → SQL

### Method
Prompt Claude with: the `v_readonly_transactions` schema, 3–5 example
question/SQL pairs, and the user question. Require a single `SELECT`.

### Guardrails
- Parse with `sqlglot`; reject if not exactly one `SELECT`, or if it references any
  object other than `v_readonly_transactions`.
- Force-append `LIMIT 500` if absent.
- Execute as Postgres role `finscope_readonly` with `SET statement_timeout = '3s'`.
- Return the rows **and** the generated SQL so the user can audit it.

### Metrics
Execution accuracy (result matches gold) and valid-SQL rate on a 25-question fixture.
Target: execution accuracy ≥ 0.80.

## 6. Responsible use notes
- FinScope describes past spending and simple projections. It is **not** financial
  advice and the UI says so.
- Only descriptions + amounts leave the machine when the natural-language query
  feature is enabled; categorization remains local.
