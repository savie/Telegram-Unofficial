"""No Ads: cegah request sponsored video ads untuk entitlement Freemium lokal."""
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = ("messenger/video/VideoAds.java",)


def patch_video_ads(source: str) -> str:
    return patch_local_premium_checks(source, (
        (
            "if (UserConfig.getInstance(currentAccount).isPremium() && MessagesController.getInstance(currentAccount).isSponsoredDisabled())",
            "if (TeleBetaFreemium.hasAllAccess(currentAccount))",
            1,
        ),
    ))
