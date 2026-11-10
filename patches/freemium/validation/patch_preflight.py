"""Preflight path dan anchor; semua pemeriksaan dilakukan sebelum penulisan."""
from pathlib import Path

class PreflightError(RuntimeError):
    pass

def require_files(root: Path, relative_paths: tuple[str, ...]) -> dict[str, Path]:
    resolved = {name: root / name for name in relative_paths}
    missing = [name for name, path in resolved.items() if not path.is_file()]
    if missing:
        raise PreflightError("Missing required upstream files: " + ", ".join(missing))
    return resolved

def require_anchor(source: str, anchor: str, label: str) -> None:
    count = source.count(anchor)
    if count != 1:
        raise PreflightError(f"{label}: expected exactly one anchor, found {count}")
