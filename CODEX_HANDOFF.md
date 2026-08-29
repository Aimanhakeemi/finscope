# Handoff to the implementation agent

The design phase is done. This repo already contains the full specification. Your job
is implementation, tests, debugging, review, and shipping — **not** redesign.

## What already exists (do not redo)

| Area | Where | Status |
| --- | --- | --- |
| Product requirements | `docs/PRD.md` | Final |
| Architecture & decisions | `docs/ARCHITECTURE.md` | Final |
| Alternate solutions & tradeoffs | `docs/ALTERNATIVES.md` | Final — don't reopen these |
| REST API contract | `docs/API_SPEC.md` | Final — build to this exactly |
| Database schema (DDL) | `docs/DB_SCHEMA.md` | Final — migration must match |
| Data dictionary & taxonomy | `docs/DATA_DICTIONARY.md` | Final |
| ML / AI design | `docs/ML.md` | Final |
| Evaluation plan & metric gates | `docs/EVALUATION.md` | Final |
| **Milestone-by-milestone build contract** | `docs/BUILD_PLAN.md` | **Your task list** |
| Synthetic data generator | `data/generate_synthetic.py` | Working, tested — keep green |
| `recurring.py` + its tests | `backend/app/recurring.py`, `backend/tests/` | Working — extend, don't rewrite |
| `anomaly.py` | `backend/app/anomaly.py` | Drafted — wire in at M2 |
| `categorize.py`, `nlq.py`, `main.py` | `backend/app/` | Skeletons — fill in per BUILD_PLAN |
| Infra | `docker-compose.yml`, `backend/Dockerfile`, `.github/workflows/ci.yml` | Skeleton — complete at M0 |

## How to proceed

1. Read, in order: `README.md`, `docs/PRD.md`, `docs/ARCHITECTURE.md`,
   `docs/API_SPEC.md`, `docs/DB_SCHEMA.md`, `docs/ML.md`, `docs/EVALUATION.md`,
   `docs/ALTERNATIVES.md`, then `docs/BUILD_PLAN.md`.
2. Work milestone by milestone (M0 → M4). **One pull request per milestone.**
3. A milestone is done only when every item under its "Definition of done" in
   `docs/BUILD_PLAN.md` is true. Do not start the next milestone until then.
4. Follow the "Ground rules" section of `docs/BUILD_PLAN.md` (deterministic tests,
   no network in tests, lint/type-check clean, Conventional Commits).
5. If a spec is ambiguous: pick the simplest reading, implement it, and record the
   assumption in the PR body. Do not stop to ask.
6. If you believe a spec is *wrong* (not just ambiguous): implement what's written,
   but flag it in the PR body with your reasoning and a proposed change to the
   relevant doc. The human decides.

## Definition of "shipped" for the whole project

- `docker compose up` runs the full app from a clean checkout.
- `data/generate_synthetic.py` → upload in the UI → dashboard, subscriptions,
  alerts, ask, and forecast all work.
- `cd backend && python -m app.eval` produces `docs/eval_report.md` and passes all
  metric gates.
- CI is green: `ruff`, `mypy`, `pytest`, frontend build, `vitest`, and the eval gate.
- README has a screenshot, the architecture diagram, and the one-command quick start.

---

## Copy-paste starter prompt for the agent

> You are the implementation agent for the FinScope project. The full design and
> specification already live in this repo under `docs/`. Do not redesign anything.
>
> Read `CODEX_HANDOFF.md`, then `docs/BUILD_PLAN.md`, then the docs it references.
> Implement milestone **M0** exactly as specified, following the Ground rules in
> `docs/BUILD_PLAN.md`. Build to `docs/API_SPEC.md` and `docs/DB_SCHEMA.md` exactly.
> Keep all tests deterministic and offline (mock the `anthropic` client; run with
> `ANTHROPIC_API_KEY` unset). When every item in the M0 "Definition of done" is
> true and CI is green, open a pull request titled `M0: scaffolding`, with a body
> that lists what you did, any assumptions you made, and anything deferred. Then
> stop and wait for review before starting M1.
