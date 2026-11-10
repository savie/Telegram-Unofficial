"""Paid Messages dan Disable Sharing: buka gate pengaturan sisi client."""
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = ("ui/PrivacyControlActivity.java",)


def patch_privacy_controls(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("getUserConfig().isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 32),
    ))
