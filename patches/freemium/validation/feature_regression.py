"""Regression guard untuk area yang wajib dipertahankan."""

PROTECTED_AREAS = ("APP_ICONS", "CUSTOM_THEMES", "CUSTOM_UI")

def assert_protected_areas_untouched(changed_paths: list[str]) -> None:
    forbidden = [p for p in changed_paths if any(token.lower() in p.lower() for token in ("app_icons", "theme", "custom_ui"))]
    if forbidden:
        raise AssertionError("Protected App Icons / Theme & UI files changed: " + ", ".join(forbidden))
