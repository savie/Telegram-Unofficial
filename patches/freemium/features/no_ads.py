"""No Ads: hentikan pemuatan sponsored video ads dan sponsored search peers."""
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = (
    "messenger/video/VideoAds.java",
    "ui/Adapters/DialogsSearchAdapter.java",
)


def patch_video_ads(source: str) -> str:
    return patch_local_premium_checks(source, (
        (
            "if (UserConfig.getInstance(currentAccount).isPremium() && MessagesController.getInstance(currentAccount).isSponsoredDisabled())",
            "if (TeleBetaFreemium.hasAllAccess(currentAccount))",
            1,
        ),
    ))


def patch_dialogs_search_adapter(source: str) -> str:
    return patch_local_premium_checks(source, (
        (
            "query == null || query.length() < 4 || UserConfig.getInstance(currentAccount).isPremium() && MessagesController.getInstance(currentAccount).isSponsoredDisabled()",
            "query == null || query.length() < 4 || TeleBetaFreemium.hasAllAccess(currentAccount) || UserConfig.getInstance(currentAccount).isPremium() && MessagesController.getInstance(currentAccount).isSponsoredDisabled()",
            1,
        ),
    ))



def patch_search_view_pager(source: str) -> str:
    """Pertahankan aksi Remove Ads native untuk entitlement Freemium lokal."""
    return patch_local_premium_checks(source, (
        ("if (UserConfig.getInstance(currentAccount).isPremium()) {", "if (TeleBetaFreemium.hasAllAccess(currentAccount) || UserConfig.getInstance(currentAccount).isPremium()) {", 1),
    ))
