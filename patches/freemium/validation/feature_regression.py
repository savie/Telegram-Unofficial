"""Regresi: Theme/UI bukan katalog entitlement, tetapi dapat menjadi dependensi fitur."""

# These names are not standalone Freemium catalog categories. Their source files
# may still be changed when an audited Premium/Business feature depends on them.
NON_CATALOG_CONCEPTS = ("THEME", "UI")
PRESERVED_FEATURES = ("APP_ICONS",)


def assert_no_standalone_theme_ui_modules(changed_paths: list[str]) -> None:
    forbidden = [
        path for path in changed_paths
        if path.replace("\\", "/").lower() in {
            "patches/freemium/features/themes.py",
            "patches/freemium/features/ui.py",
        }
    ]
    if forbidden:
        raise AssertionError(
            "Theme/UI must not become standalone entitlement modules: "
            + ", ".join(forbidden)
        )
