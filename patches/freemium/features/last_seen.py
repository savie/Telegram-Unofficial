"""Last Seen Times: buka gate tampilan lokal tanpa memalsukan data server."""
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = ("ui/Components/MessagePrivateSeenView.java",)


def patch_message_private_seen_view(source: str) -> str:
    return patch_local_premium_checks(source, (
        (
            "final boolean premiumLocked = MessagesController.getInstance(currentAccount).premiumFeaturesBlocked();",
            "final boolean premiumLocked = MessagesController.getInstance(currentAccount).premiumFeaturesBlocked() && !TeleBetaFreemium.hasAllAccess(currentAccount);",
            1,
        ),
    ))
