# FinScope

FinScope is a local-first personal spending intelligence app for CSV import,
categorization, dashboards, recurring-charge detection, anomaly alerts,
natural-language SQL, and forecasting.

The LLM (Claude) is allowed only in the natural-language query feature. It must
never touch categorization, anomaly detection, or forecasting. Categorization is
rules plus a local scikit-learn model; recurring, anomaly, and forecasting logic
is local code.

Milestones: M0 scaffold; M1 import + categorize + dashboard; M2 recurring +
anomaly; M3 NL-query + forecast; M4 evaluation.

See [docs/BUILD_PLAN.md](docs/BUILD_PLAN.md) for the implementation contract.
