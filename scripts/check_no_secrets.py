#!/usr/bin/env python3
"""Fail CI when hardcoded secrets are detected in committed source."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ecs.core.secrets_audit import scan_for_secrets  # noqa: E402


def main() -> int:
    findings = scan_for_secrets(REPO_ROOT)
    if not findings:
        print("No hardcoded secrets detected.")
        return 0

    print("Hardcoded secret patterns detected:", file=sys.stderr)
    for finding in findings:
        print(
            f"  {finding.path}:{finding.line_number} [{finding.rule}] {finding.excerpt}",
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
