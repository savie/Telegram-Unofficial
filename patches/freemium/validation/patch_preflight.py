"""Preflight source, revision upstream, dan anchor sebelum patch dijalankan."""
from pathlib import Path
import re


class PreflightError(RuntimeError):
    pass


def require_files(root: Path, relative_paths: tuple[str, ...]) -> dict[str, Path]:
    resolved = {name: root / name for name in relative_paths}
    missing = [name for name, path in resolved.items() if not path.is_file()]
    if missing:
        raise PreflightError("Missing required upstream files: " + ", ".join(missing))
    return resolved


def require_upstream_revision(repo_root: Path) -> str:
    revision_file = repo_root / "UPSTREAM_TELEGRAM_COMMIT"
    if not revision_file.is_file():
        raise PreflightError("Missing UPSTREAM_TELEGRAM_COMMIT")
    revision = revision_file.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise PreflightError("UPSTREAM_TELEGRAM_COMMIT must contain one full 40-character SHA")
    return revision


def require_anchor(source: str, anchor: str, label: str) -> None:
    count = source.count(anchor)
    if count != 1:
        raise PreflightError(f"{label}: expected exactly one anchor, found {count}")
