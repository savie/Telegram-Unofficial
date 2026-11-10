"""Wallpaper for Both Sides: buka gate apply-to-both pada editor upstream."""
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = ("ui/ThemePreviewActivity.java",)


def patch_theme_preview_activity(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("getUserConfig().isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 2),
    ))
