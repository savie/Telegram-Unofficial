"""Name and Profile Colors, Profile Badge, serta jalur profil Premium."""
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = ("ui/PeerColorActivity.java", "ui/ProfileActivity.java")


def patch_peer_color_activity(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("getUserConfig().isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 5),
    ))


def patch_profile_activity(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("getUserConfig().isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 5),
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 3),
    ))
