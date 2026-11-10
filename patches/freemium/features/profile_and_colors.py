"""Name and Profile Colors serta Profile Badge; tidak membuat kategori Theme/UI."""
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = ("ui/PeerColorActivity.java",)


def patch_peer_color_activity(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("getUserConfig().isPremium()",
         "TeleBetaFreemium.hasAllAccess(currentAccount)", 5),
    ))
