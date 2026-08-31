# FinScope — Alternate Solution Review & Design Tradeoffs

This document records the alternatives that were considered and why the current
choice was made, so the reasoning is not lost.

Format: for each decision — the options, the axes that matter, the choice, and the
cost we accept by choosing it.

---

## Part A — Alternate app concepts (why FinScope at all)

The brief was: one small app that demonstrates software engineering + data analysis
+ AI engineering, solves a real problem, and is simple but interesting.

| Concept | Real problem | Why it shows the 3 skills | Why NOT chosen |
| --- | --- | --- | --- |
| **FinScope** — statement → spending insight, subscription finder, NL questions | Everyone has a messy bank statement; forgotten subscriptions cost real money | ETL + stats (analysis), API/DB/UI (SWE), classifier + NL→SQL + eval (AI) | *Chosen* |
| Receipt-photo expense tracker | Manual expense entry is tedious | OCR + LLM extraction is a strong AI story | OCR adds a hard, noisy dependency; demo needs real photos; less *data analysis*, more *computer vision* |
| Job-posting skill-gap analyzer | Job seekers don't know what to learn next | Scraping + LLM extraction + market trend analysis | Data is scraped (fragile, ToS grey area); harder to make deterministic/testable |
| Personal habit / time-tracker analytics | People want to understand their time | Time-series analysis is clean | Weak AI-engineering angle; no natural LLM feature that isn't bolted on |
| Support-ticket triage / tagging tool | Teams drown in unlabeled tickets | Classification + routing + eval is a clean AI story | Needs a plausible ticket dataset; "business tool" framing is less relatable in a portfolio |

**Deciding axis:** FinScope is the only concept where all three skills are *load-bearing*
(remove any one and the app stops being useful), the input is a file anyone can
produce, and the whole thing can run deterministically from synthetic data.

**Cost accepted:** "personal finance app" is a crowded category, so the project has to
compete on *execution quality and the evaluation harness*, not novelty.

---

## Part B — Component-level decisions

### B1. Transaction categorization

| Option | Accuracy | Cost / latency | Deterministic? | Cold start | Notes |
| --- | --- | --- | --- | --- | --- |
| Pure regex rules | Low–med | Free, instant | Yes | Fine | Breaks on unseen merchants; endless rule maintenance |
| LLM on every transaction | High | $ per txn, slow, rate limits | No | Fine | Great accuracy, bad for a demo that must run offline and in CI |
| **Rules + local model (TF-IDF + LogReg), no LLM** | Med–high | Free, local, fast | Yes | Weak until corrections accumulate | *Chosen* |
| Fine-tuned small transformer | High | Training infra, longer CI | Yes | Weak | Overkill for ~2–5k rows; harder to justify in a portfolio review |
| Sentence-embeddings + kNN | Med–high | Model download (~100MB), fast inference | Yes | Weak | Kept as a **stretch** — swap it in and compare in the eval report |

**Long-form reasoning.** Rules handle obvious merchants and the local model handles
unseen strings. Low-confidence rows are flagged for manual review, and corrections
become labels for the next retrain. This preserves a deterministic, offline path
that is straightforward to audit.

The project constraint is deliberate: keeping the LLM auditable and limited to
natural-language queries means categorization never gains a hidden network or cost
dependency. The cost accepted is lower confidence on unseen merchants and the
manual review time needed to improve the training set.

### B2. Recurring-payment detection

| Option | Explainable? | Works on small data? | Effort |
| --- | --- | --- | --- |
| **Group by merchant → inter-arrival gap analysis + amount-stability check** | Fully | Yes | Low | *Chosen* |
| Autocorrelation / FFT on a daily spend series per merchant | Somewhat | Needs long history | Med | Elegant but fragile with 6–12 sparse points per merchant |
| Train a classifier on (merchant features → is_recurring) | No | No (tiny label set) | Med | Can't justify ML here; nothing to learn from |

**Reasoning.** The signal is explicit: a subscription is "same payee, regular gap,
stable amount". Encoding that as three thresholds is more honest than dressing it up
as ML, and every flag comes with a human-readable reason. Deliberately *not* an AI
feature — and saying so in the docs is itself a signal of judgement.

**Cost accepted:** misses irregular-but-real recurring costs (quarterly taxes with
drifting amounts, annual renewals seen only once in the window). Documented as a
known limitation.

### B3. Anomaly detection

| Option | False-positive control | Explainable | Notes |
| --- | --- | --- | --- |
| **Per-category robust z-score (median/MAD) + IQR fence + "new large merchant", require ≥2 signals** | Good (the 2-signal rule) | Yes | *Chosen*; recurring txns excluded first |
| `IsolationForest` / `LocalOutlierFactor` | Hard to tune on small n | No | Black-box flags are useless to a user ("why is this weird?") |
| Prophet/ETS residual outliers | Decent | Partial | Needs a trained series per category; heavy for the payoff |

**Reasoning.** A finance user needs a *reason*, not just a flag. Robust statistics
give one ("4× your typical grocery spend"). The ≥2-signal rule is the tuning knob
that keeps the alert list short enough to be read.

**Cost accepted:** will miss a subtle anomaly that only one signal catches. Acceptable
— a tool that cries wolf gets ignored.

### B4. Natural-language questions

| Option | SWE/SQL skill shown | Safety | Flexibility | Notes |
| --- | --- | --- | --- | --- |
| **LLM → single SELECT over a locked-down read-only view, parsed + limited + timed** | High (real least-privilege design) | Good | High | *Chosen* |
| Predefined parameterized queries, LLM only picks intent + fills slots | Med | Excellent | Low (fixed question set) | Safer but boring; doesn't show SQL range |
| Semantic layer (dbt metrics / cube.dev) | Med | Good | Med | Large dependency for a personal app |
| Off-the-shelf text-to-SQL framework | Low | Depends | High | Hides the interesting part behind a library |

**Long-form reasoning.** The security posture *is* the portfolio content here:
a dedicated Postgres role with `SELECT` on exactly one view, a `sqlglot` parse that
rejects anything but a lone `SELECT` touching only that view, a forced `LIMIT`, and a
`statement_timeout`. That's a realistic answer to "how do you let an LLM near a
database safely", and it's more impressive than a broader but unguarded text-to-SQL.

**Cost accepted:** some legitimate questions won't be answerable through one view
(anything needing joins or history the view hides). The UI shows the generated SQL so
the user can see *why* an answer looks the way it does.

### B5. Overall architecture

| Option | Fits scope? | Reviewability | Notes |
| --- | --- | --- | --- |
| **Modular monolith** (one FastAPI process, independent modules per capability) | Yes | High — one repo, one process to run | *Chosen* |
| Microservices (separate categorizer / analytics / nlq services) | No | Low — infra noise drowns the actual work | Reviewers would ask "why?" and be right |
| Serverless functions | Partial | Med | Cold starts, local-dev friction, state handling awkward |
| Notebook / Streamlit script only | Partial | Low | Fast to build, but hides the SWE skills the portfolio needs to show |

### B6. Database

| Option | Analytics ergonomics | NL→SQL story | Ops |
| --- | --- | --- | --- |
| **PostgreSQL** | Good (window functions, views, roles) | Strong — real roles/grants for the guardrail | One container |
| SQLite | OK | Weak — no real per-role privilege separation | Zero setup |
| DuckDB | Excellent for analytics | Medium — great SQL, weaker multi-user/permission model | Embedded |

**Reasoning.** DuckDB is genuinely tempting for the analytics workload and would be a
defensible choice. Postgres wins because the **NL→SQL guardrail demo depends on a
real privilege system** (`finscope_readonly` role, `GRANT SELECT` on one view) — that
story is much weaker in SQLite/DuckDB. Also, "I ran Postgres with migrations" is a
more standard SWE signal.

**Cost accepted:** a container and a migration tool to set up. Worth it.

### B7. Backend language

Python chosen so the API, the pandas ETL, the scikit-learn model, and the eval
harness are all one language and one test suite. Node or Go would mean a second
runtime just for the ML/analysis code, or reaching for weaker libraries. The cost:
Python's packaging and type-checking story is rougher — mitigated with pinned
`requirements.txt`, `ruff`, and `mypy` in CI.

### B8. Frontend

React + TypeScript chosen over Streamlit/Gradio. Streamlit would cut the frontend
work by ~70%, but the portfolio explicitly needs to show software-engineering
breadth, and "typed component, tested with Vitest, built in CI" is part of that.
The cost: real frontend time (~2–3 days across milestones). Kept small — 5 screens,
3 chart components, one table component.

### B9. Deployment

Local `docker compose up` is the target. A live hosted demo (Fly.io/Render) is a
**stretch** goal, not a requirement, because hosting a finance-flavoured app invites
questions about data handling that aren't worth answering for a portfolio piece.
Synthetic-data-only + "run it yourself in one command" sidesteps all of it.

---

## Part C — The three tradeoffs most likely to be questioned

1. **"Why not just use an LLM for everything?"** — Cost, latency, determinism,
   offline/CI runnability, and because the routing decision is the part worth
   showing. See B1.
2. **"Isn't rule-based recurring detection too simple?"** — Yes, deliberately. The
   signal is explicit and every result is explainable. Adding ML here would be
   resume-driven design. See B2.
3. **"Why Postgres and not something lighter?"** — The NL→SQL safety story needs a
   real privilege system. See B6.

---

## Part D — Explicitly out of scope (and why)

| Not doing | Why |
| --- | --- |
| Real bank aggregation (Plaid) beyond a sandbox stretch | Auth complexity, secrets handling, no payoff for a portfolio |
| Multi-currency / FX | Doubles the data model for a niche case |
| Investment / net-worth tracking | Different problem, different data |
| Multi-tenant SaaS hardening (billing, rate limits, org roles) | Not what the portfolio is demonstrating |
| Mobile app | Second frontend for no additional signal |
| Tax categorization / reporting | Jurisdiction-specific, high accuracy bar, liability |
