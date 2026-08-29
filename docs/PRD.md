# FinScope — Product Requirements

## 1. Problem statement

Individuals cannot easily answer three questions from their own bank data:
"What am I subscribed to?", "Was any charge unusual?", and "Where did my money go?"
Existing tools require manual categorization or a bank login most people are wary of.

## 2. Goals

- G1: From a CSV upload, categorize ≥90% of transactions correctly with no user input.
- G2: Detect recurring charges (subscriptions, rent, utilities) with ≥0.85 precision
  and ≥0.80 recall on the labeled fixture.
- G3: Flag anomalous transactions with a false-positive rate low enough to be useful
  (≤1 false alert per 100 transactions on the fixture).
- G4: Answer natural-language questions with ≥80% execution accuracy on the NL→SQL fixture.
- G5: Whole system runs locally with `docker compose up` and synthetic data.

## 3. Non-goals

- Real bank aggregation / Plaid (stretch only).
- Multi-currency, investments, tax reporting.
- Mobile app.
- Multi-tenant SaaS hardening (rate limiting, billing).

## 4. Users & primary flows

**Persona: "Budget-curious individual"** — has a messy statement, wants insight in 2 minutes.

1. **Import**: upload CSV → system normalizes, dedupes, categorizes, stores.
2. **Review dashboard**: spend by category, monthly trend, top merchants.
3. **Subscriptions view**: list of detected recurring charges with cadence, next
   expected date, monthly cost, "haven't used?" prompt.
4. **Alerts**: anomalies for the latest period.
5. **Ask**: free-text question → answer + the SQL that produced it + a small table/chart.
6. **Forecast**: projected total spend and per-category spend for next month with a range.

## 5. Functional requirements

| ID | Requirement |
| --- | --- |
| F1 | Accept CSV with headers mappable to `date`, `description`, `amount`; support common bank variants via a column-mapping step |
| F2 | Normalize: parse dates, sign amounts (debits negative), strip merchant noise ("SQ *", store numbers, city/state) |
| F3 | Deduplicate on `(date, normalized_description, amount)` within an import and across imports |
| F4 | Categorize into a fixed taxonomy (see DATA_DICTIONARY); store category + confidence + source (`model` \| `llm` \| `rule` \| `user`) |
| F5 | User can correct a category; corrections are persisted and used as future training labels |
| F6 | Recurring detection groups transactions by merchant and finds stable inter-arrival periods (weekly/biweekly/monthly/quarterly/annual) |
| F7 | Anomaly detection per category using robust statistics; also flag first-time large merchants |
| F8 | Forecast next-month total and top-category spend with a prediction interval |
| F9 | NL→SQL: translate a question to a read-only SQL query, execute against a restricted view, return rows + generated SQL |
| F10 | REST API documented via OpenAPI; every analytic also callable directly |

## 6. Quality / non-functional

- Deterministic tests (seeded synthetic data, pinned model artifact).
- LLM features degrade gracefully: if `ANTHROPIC_API_KEY` is absent, categorization
  uses model+rules only and NL→SQL returns a clear "LLM disabled" message.
- NL→SQL runs only `SELECT` against a whitelisted read-only role; queries are
  timeout- and row-limited.
- No secrets in the repo; `.env.example` documents all config.

## 7. Success metric for the portfolio

A reviewer can, in 10 minutes: run it, upload the sample, see insights, read
`docs/eval_report.md` with real numbers, and understand the design from
`docs/ARCHITECTURE.md`.

## 8. Milestones

See [ROADMAP.md](ROADMAP.md). M1 (import + categorize + dashboard) is the minimum
shippable portfolio piece; M2 adds recurring + anomalies; M3 adds NL→SQL + forecast;
M4 is polish + eval report.
