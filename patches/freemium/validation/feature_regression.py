"""Regresi katalog resmi dan preservasi batas Theme/UI."""
from ..catalog.business_catalog import BUSINESS_CATALOG
from ..catalog.premium_catalog import PREMIUM_CATALOG
from ..integration.business_feature_gates import BUSINESS_GATE_TARGETS
from ..integration.premium_feature_gates import PREMIUM_GATE_TARGETS

NON_CATALOG_CONCEPTS = ("THEME", "UI")
PRESERVED_FEATURES = ("APP_ICONS",)


def validate_catalog_mapping() -> None:
    missing_premium = set(PREMIUM_CATALOG) - set(PREMIUM_GATE_TARGETS)
    extra_premium = set(PREMIUM_GATE_TARGETS) - set(PREMIUM_CATALOG)
    missing_business = set(BUSINESS_CATALOG) - set(BUSINESS_GATE_TARGETS)
    extra_business = set(BUSINESS_GATE_TARGETS) - set(BUSINESS_CATALOG)
    if missing_premium or extra_premium or missing_business or extra_business:
        raise AssertionError(
            "Catalog/source mapping mismatch: "
            f"premium_missing={sorted(missing_premium)}, "
            f"premium_extra={sorted(extra_premium)}, "
            f"business_missing={sorted(missing_business)}, "
            f"business_extra={sorted(extra_business)}"
        )


def assert_no_standalone_theme_ui_modules(changed_paths: list[str]) -> None:
    forbidden = [
        path for path in changed_paths
        if path.replace("\\", "/").lower() in {
            "patches/freemium/features/themes.py",
            "patches/freemium/features/ui.py",
            "patches/freemium/integration/theme.py",
            "patches/freemium/integration/ui.py",
        }
    ]
    if forbidden:
        raise AssertionError(
            "Theme/UI must not become standalone entitlement modules: "
            + ", ".join(forbidden)
        )
