"""Unit tests for the committed-source secrets audit."""

from __future__ import annotations

from pathlib import Path

from ecs.core.secrets_audit import scan_for_secrets

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_repo_source_tree_has_no_hardcoded_secrets() -> None:
    findings = scan_for_secrets(REPO_ROOT)
    assert findings == [], "\n".join(
        f"{finding.path}:{finding.line_number} [{finding.rule}] {finding.excerpt}"
        for finding in findings
    )


def test_scanner_flags_embedded_sql_password(tmp_path: Path) -> None:
    sample = tmp_path / "src" / "sample.py"
    sample.parent.mkdir(parents=True)
    sample.write_text(
        'CONNECTION = "Server=prod;Database=ecs;User ID=app;Password=SuperSecret123;"\n',
        encoding="utf-8",
    )

    findings = scan_for_secrets(tmp_path)

    assert len(findings) == 1
    assert findings[0].rule == "SQL password assignment"
