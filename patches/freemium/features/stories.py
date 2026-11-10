"""Stories: buka gate lokal Stealth Mode dan riwayat penonton kedaluwarsa."""
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = (
    "ui/Stories/StealthModeAlert.java",
    "ui/Stories/SelfStoryViewsPage.java",
)


def patch_stealth_mode(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()",
         "TeleBetaFreemium.hasAllAccess(currentAccount)", 1),
    ))


def patch_expired_story_views(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()",
         "TeleBetaFreemium.hasAllAccess(currentAccount)", 2),
    ))
