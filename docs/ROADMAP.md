# FinScope — Roadmap

This roadmap breaks the work into milestones. Each milestone is a shippable,
demoable state.

## M0 — Scaffolding (½ day)
- [ ] Repo, `docker-compose.yml`, `.env.example`, CI skeleton
- [ ] Postgres + Alembic initial migration (schema from DATA_DICTIONARY)
- [ ] `data/generate_synthetic.py` producing statement + labels
- [ ] FastAPI app with `/healthz`

## M1 — Import + categorize + dashboard (2–3 days)  ← minimum portfolio piece
- [ ] `POST /api/imports` — CSV upload, column mapping, ETL, dedupe
- [ ] `categorize.py` — TF-IDF + LogisticRegression + rules; persist artifact
- [ ] `GET /api/analytics/summary` — category totals, monthly series, top merchants
- [ ] React dashboard: upload flow + 3 charts (Recharts)
- [ ] `PATCH /api/transactions/{id}` — category correction
- [ ] pytest for ETL + categorizer; Vitest for the upload component

## M2 — Recurring + anomalies (2 days)
- [ ] `recurring.py` (already drafted) wired into the import pipeline
- [ ] `GET /api/subscriptions` — detected recurring groups + next expected date
- [ ] `anomaly.py` + `GET /api/alerts`
- [ ] Subscriptions view + Alerts view in the UI
- [ ] Tests against `anomaly_truth.csv` and label recurring flags

## M3 — NL→SQL + forecast (2–3 days)
- [ ] `finscope_readonly` role + `v_readonly_transactions` view + migration
- [ ] `nlq.py` — Claude prompt, `sqlglot` guardrail, timeout/limit execution
- [ ] `POST /api/ask` — returns rows + generated SQL
- [ ] `forecast.py` + `GET /api/forecast`
- [ ] "Ask" box and forecast card in the UI
- [ ] `nlq_cases.yaml` fixture (25 cases)

## M4 — Evaluation + polish (1–2 days)
- [ ] `app/eval.py` — full harness, Markdown report, CI gate
- [ ] Commit a real `docs/eval_report.md`
- [ ] README screenshots + architecture diagram
- [ ] `ruff`, `mypy`, `pre-commit`
- [ ] MIT `LICENSE`, `CONTRIBUTING.md`

## Stretch (optional)
- [ ] Plaid sandbox import as an alternative to CSV
- [ ] Category-level budgets + "on track / over" indicator
- [ ] Deploy to Fly.io/Render with a live demo link
- [ ] Swap LogisticRegression for a small embedding model + kNN and compare in the report
- [ ] Export monthly report as PDF

## Estimated total: ~2 weeks part-time for M0–M4.
