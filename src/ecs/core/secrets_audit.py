"""Static analysis helpers to detect hardcoded secrets in committed source."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SCAN_ROOTS = ("src", "sql", "scripts")
DEFAULT_EXCLUDED_DIR_NAMES = {
    "__pycache__",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "venv",
}
DEFAULT_EXCLUDED_FILE_SUFFIXES = (".pyc", ".pyo")
DEFAULT_ALLOWED_FILE_SUFFIXES = (
    ".py",
    ".sql",
    ".bicep",
    ".json",
    ".yml",
    ".yaml",
    ".sh",
    ".ps1",
)
DEFAULT_EXCLUDED_FILE_NAMES = {
    "local.settings.json",
    "local.settings.json.example",
}

_SECRET_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"Password\s*=\s*[^;\s\"']+", re.IGNORECASE), "SQL password assignment"),
    (re.compile(r"AccountKey\s*=\s*\S+", re.IGNORECASE), "storage account key"),
    (re.compile(r"SharedAccessKey\s*=\s*\S+", re.IGNORECASE), "shared access key"),
    (
        re.compile(
            r"DefaultEndpointsProtocol=https?://",
            re.IGNORECASE,
        ),
        "Azure storage connection string",
    ),
    (
        re.compile(
            r"mssql(\+pyodbc)?://[^/\s\"']+:[^@\s\"']+@",
            re.IGNORECASE,
        ),
        "SQLAlchemy URL with embedded credentials",
    ),
    (
        re.compile(
            (
                r"Driver=\{[^}]+\};Server=[^;]+;"
                r"(?:Database|Initial Catalog)=[^;]+;"
                r"(?:User ID|UID)=[^;]+;Password="
            ),
            re.IGNORECASE,
        ),
        "ODBC connection string with SQL authentication",
    ),
)


@dataclass(frozen=True, slots=True)
class SecretFinding:
    """A single suspected secret embedded in a scanned file."""

    path: Path
    line_number: int
    rule: str
    excerpt: str


def _iter_scan_files(
    repo_root: Path,
    *,
    scan_roots: tuple[str, ...] = DEFAULT_SCAN_ROOTS,
) -> list[Path]:
    files: list[Path] = []
    for root_name in scan_roots:
        root = repo_root / root_name
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in DEFAULT_EXCLUDED_DIR_NAMES for part in path.parts):
                continue
            if path.name in DEFAULT_EXCLUDED_FILE_NAMES:
                continue
            if path.suffix.lower() in DEFAULT_EXCLUDED_FILE_SUFFIXES:
                continue
            if path.suffix and path.suffix.lower() not in DEFAULT_ALLOWED_FILE_SUFFIXES:
                continue
            files.append(path)
    return sorted(files)


def scan_for_secrets(
    repo_root: Path | str,
    *,
    scan_roots: tuple[str, ...] = DEFAULT_SCAN_ROOTS,
) -> list[SecretFinding]:
    """Return findings for suspected hardcoded secrets under scan roots."""
    root = Path(repo_root)
    findings: list[SecretFinding] = []

    for file_path in _iter_scan_files(root, scan_roots=scan_roots):
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue

        for line_number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            for pattern, rule in _SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append(
                        SecretFinding(
                            path=file_path.relative_to(root),
                            line_number=line_number,
                            rule=rule,
                            excerpt=stripped[:120],
                        )
                    )
                    break

    return findings
