"""Paid Messages dan Disable Sharing: buka gate pengaturan sisi client."""
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = ("ui/PrivacyControlActivity.java", "ui/PrivacySettingsActivity.java")


def patch_privacy_controls(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("getUserConfig().isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 32),
    ))



def patch_privacy_settings_activity(source: str) -> str:
    return patch_local_premium_checks(source, (
        (
            "!getMessagesController().premiumFeaturesBlocked() || getUserConfig().isPremium()",
            "!getMessagesController().premiumFeaturesBlocked() || TeleBetaFreemium.hasAllAccess(currentAccount)",
            1,
        ),
        (
            "getMessagesController().autoarchiveAvailable || getUserConfig().isPremium()",
            "getMessagesController().autoarchiveAvailable || TeleBetaFreemium.hasAllAccess(currentAccount)",
            1,
        ),
        ("!getUserConfig().isPremium()", "!TeleBetaFreemium.hasAllAccess(currentAccount)", 1),
    ))
