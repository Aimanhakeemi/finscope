# Contributing to FinScope

## Setup

The full stack runs with Docker:

```bash
cp .env.example .env
docker compose up --build
```

For backend-only work, create a Python 3.11 virtual environment and install
`backend/requirements.txt`:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

## Checks

```bash
pytest backend -q
cd backend && python -m app.eval --report ../docs/eval_report.md
```

The evaluation harness is deterministic, offline, and must finish with all
gates passing. Keep `ANTHROPIC_API_KEY` unset for tests and evaluation.

## Ground rules

Use one branch and pull request per milestone. Use Conventional Commits, keep
tests deterministic, and do not change the taxonomy, API shapes, or database
schema without updating the authoritative docs in the same change. See
`docs/ROADMAP.md` for the milestone plan.

The LLM is used only for the NL→SQL feature. Categorization, recurring and
anomaly detection, forecasting, and evaluation must remain local and offline.
