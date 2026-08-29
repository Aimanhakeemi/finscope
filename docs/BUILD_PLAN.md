# FinScope — Build Plan (implementation-agent facing)

This is the contract for the implementation agent (Codex). Each milestone is a PR.
A milestone is **done** only when every item in its "Definition of done" is true.

Read first: `README.md`, `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/API_SPEC.md`,
`docs/DB_SCHEMA.md`, `docs/ML.md`, `docs/EVALUATION.md`, `docs/ALTERNATIVES.md`.

## Ground rules

- **Do not change** the category taxonomy, the API shapes in `API_SPEC.md`, or the
  schema in `DB_SCHEMA.md` without saying so in the PR description and updating that
  doc in the same PR.
- Keep tests **deterministic**: seeded synthetic data, `ANTHROPIC_API_KEY` unset in
  CI, no network calls in tests (mock the `anthropic` client).
- Every module gets unit tests. Every endpoint gets one happy-path + one error test.
- Python: `ruff` clean, `mypy` clean on `backend/app` (may use `# type: ignore` sparingly
  with a reason). TS: `tsc --noEmit` clean.
- Conventional Commits. One PR per milestone; PR body links the milestone here and
  lists what was and wasn't done.
- If a spec is ambiguous, pick the simplest interpretation, implement it, and note the
  assumption in the PR body. Do not block.

---

## M0 — Scaffolding

**Files**
- `backend/pyproject.toml` or keep `requirements.txt` (already present) + `backend/setup.cfg` for tools
- `backend/alembic.ini`, `backend/migrations/env.py`, `backend/migrations/versions/0001_initial.py`
- `backend/app/db.py` — engine, session, `get_session` dependency, plus a separate
  read-only engine factory
- `backend/app/config.py` — pydantic-settings, reads env from `.env`
- `backend/app/models.py` — SQLAlchemy models mirroring `DB_SCHEMA.md`
- `backend/app/seed.py` — insert the demo user on startup if absent
- `backend/tests/conftest.py` — test DB (testcontainers or a `finscope_test` DB), fixtures
- `frontend/` — `npm create vite` React+TS, Tailwind, Vitest, `src/api/client.ts`
- `.pre-commit-config.yaml`
- Wire `app/eval.py` as an empty CLI stub (`python -m app.eval` prints "not implemented")

**Definition of done**
- `docker compose up` starts db + api + web with no errors
- `alembic upgrade head` produces exactly the schema in `DB_SCHEMA.md` (verify with a
  schema-dump test)
- `GET /healthz` returns the documented body
- `python data/generate_synthetic.py` runs (already works — keep it green)
- `pytest backend -q` and `npm test -- --run` both pass in CI
- CI workflow green on the branch

---

## M1 — Import + categorize + dashboard  ← minimum shippable

**Backend files**
- `backend/app/etl.py` — `normalize(raw_bytes, mapping) -> DataFrame`; date parsing,
  amount signing, merchant cleaning, dedupe. Move the logic currently inline in
  `main.py` here and test it.
- `backend/app/categorize.py` — finish the skeleton: real `Categorizer` with a
  `train(df) -> None` and `predict_one`; persist `app/artifacts/categorizer.joblib`
- `backend/app/train_categorizer.py` — CLI: build the model from synthetic labels +
  any `category_corrections`, write the artifact + sidecar JSON
- `backend/app/routes/imports.py`, `routes/transactions.py`, `routes/analytics.py`
- `backend/app/services/import_service.py` — orchestrates ETL → categorize → persist
- Update `backend/app/main.py` to include routers; remove the ad-hoc logic

**Frontend files**
- `src/pages/Import.tsx` — file picker, optional column-mapping form, POST, result summary
- `src/pages/Dashboard.tsx`
- `src/components/CategoryBarChart.tsx`, `MonthlyTrendChart.tsx`, `DataTable.tsx`
- `src/api/client.ts` — typed methods for the M1 endpoints
- Routing (`react-router-dom`), a nav shell

**Tests**
- `test_etl.py` — date formats, debit/credit columns, dedupe, bad input → 400
- `test_categorize.py` — rules fire; model path; low-confidence path with a **mocked**
  anthropic client; taxonomy-only outputs
- `test_imports_api.py`, `test_analytics_api.py`
- `Import.test.tsx` — renders, submits, shows summary (mock fetch)

**Definition of done**
- Upload `data/sample_statement.csv` via UI → see category breakdown + 3 charts
- `PATCH /api/transactions/{id}` persists a correction and flips `category_source` to `user`
- `GET /api/analytics/summary` matches `API_SPEC.md` shape exactly
- Categorizer artifact committed OR rebuilt in CI before tests; document which
- All M0 DoD still true

---

## M2 — Recurring + anomalies

**Files**
- `backend/app/anomaly.py` — already drafted; wire it, keep the ≥2-signal rule
- `backend/app/services/enrich_service.py` — post-import job: run `detect_recurring`
  over the user's full history, upsert `recurring_groups`, set `is_recurring` /
  `recurring_group_id`; then `detect_anomalies` on non-recurring txns, set
  `is_anomaly` / `anomaly_reason`
- `backend/app/routes/subscriptions.py`, `routes/alerts.py`
- `src/pages/Subscriptions.tsx`, `src/pages/Alerts.tsx`
- `backend/tests/fixtures/anomaly_truth.csv` — ids/keys of the injected anomalies from
  the synthetic generator (BIG APPLIANCE WAREHOUSE, OVERSEAS ATM WITHDRAWAL, the dup)

**Tests**
- `test_recurring.py` already exists — extend to run against the synthetic labels file
  and assert precision ≥ 0.85, recall ≥ 0.80
- `test_anomaly.py` — against `anomaly_truth.csv`: precision ≥ 0.70, ≤ 1 false alert / 100
- `test_subscriptions_api.py`, `test_alerts_api.py`

**Definition of done**
- After import, `GET /api/subscriptions` lists Netflix/Spotify/etc. with correct
  cadence and a `next_expected` date; `price_changed` true for Netflix
- `GET /api/alerts` returns the injected anomalies and not much else
- Rent/utilities do **not** appear as anomalies (excluded as recurring)
- UI: Subscriptions view shows total monthly cost; Alerts view lists flagged txns with reasons

---

## M3 — NL→SQL + forecast

**Files**
- `backend/migrations/versions/0002_readonly_role.py` — `v_readonly_transactions`,
  `finscope_readonly` role + grants + `statement_timeout`
- `backend/app/nlq.py` — finish: `generate_sql`, `validate_sql` (sqlglot guardrail),
  `run_readonly(sql) -> (columns, rows)` using the read-only engine
- `backend/app/routes/ask.py` — `POST /api/ask`; 503 when LLM disabled
- `backend/app/forecast.py` — ETS / seasonal-naive / trailing-median per `ML.md`
- `backend/app/routes/forecast.py`
- `backend/tests/fixtures/nlq_cases.yaml` — 25 cases: `{question, gold_sql?, gold_result}`
- `src/pages/Ask.tsx` — question box, renders answer table + the generated SQL (read-only)
- `src/components/ForecastCard.tsx`, add to Dashboard

**Tests**
- `test_nlq_guardrail.py` — rejects: multiple statements, non-SELECT, other tables,
  `pg_sleep`, missing LIMIT gets one injected
- `test_nlq_cases.py` — runs the 25 fixtures with a **mocked** SQL generator (fixture
  provides the SQL) against a seeded DB; execution accuracy ≥ 0.80
- `test_forecast.py` — shape + fallback selection by history length

**Definition of done**
- With a real key: "how much on coffee since June?" returns a number + visible SQL
- Without a key: `/api/ask` returns 503 with the documented message; nothing crashes
- Guardrail test suite fully green
- `GET /api/forecast` matches `API_SPEC.md`

---

## M4 — Evaluation harness + polish

**Files**
- `backend/app/eval.py` — full harness per `docs/EVALUATION.md`: regenerate synthetic
  data, run the pipeline, compute every metric, write `docs/eval_report.md`, exit
  non-zero if a gate regresses
- Add the eval step to `.github/workflows/ci.yml` (currently commented out)
- `CONTRIBUTING.md`, ensure `LICENSE` present (it is)
- README: add real screenshots (`docs/img/`), confirm the mermaid diagram renders
- `docs/eval_report.md` — committed from a real run

**Definition of done**
- `cd backend && python -m app.eval --report ../docs/eval_report.md` produces the
  report and exits 0 with all gates passing
- CI runs the eval and fails on a deliberately introduced regression (test this once)
- README top section: one screenshot + the diagram + the quick-start
- `ruff`, `mypy`, `pre-commit`, both test suites green

---

## Stretch (only after M4, separate PRs)

Plaid sandbox import · category budgets · hosted demo · embeddings+kNN categorizer
compared in the eval report · PDF monthly report. See `docs/ROADMAP.md`.
