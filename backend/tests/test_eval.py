from __future__ import annotations

from pathlib import Path

from app import eval as evaluation


def test_eval_runs_end_to_end_and_writes_report(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    report = tmp_path / "eval_report.md"

    assert evaluation.main(["--report", str(report)]) == 0
    contents = report.read_text(encoding="utf-8")
    assert "# FinScope Evaluation Report" in contents
    assert "## Summary" in contents
    assert "## Categorizer confusion matrix" in contents
    assert "## Ablations" in contents
    assert "Confidence threshold sweep" in contents
    assert "PASS" in contents


def test_eval_returns_nonzero_when_a_gate_regresses(tmp_path: Path, monkeypatch, capsys):
    result = evaluation.run_evaluation()
    result.metrics["categorizer_accuracy"] = 0.0
    monkeypatch.setattr(evaluation, "run_evaluation", lambda: result)

    assert evaluation.main(["--report", str(tmp_path / "failed.md")]) == 1
    assert "categorizer_accuracy=0.0000" in capsys.readouterr().out
