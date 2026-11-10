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
    """Hapus sponsored search ads secara lokal tanpa memanggil API disableAds."""
    old = """if (UserConfig.getInstance(currentAccount).isPremium()) {
                            fragment.getMessagesController().disableAds(true);
                            removeAllAds();
                            BulletinFactory.of(fragment)
                                .createAdReportedBulletin(LocaleController.getString(R.string.AdHidden))
                                .show();
                        } else {
                            new PremiumFeatureBottomSheet(fragment, PremiumPreviewFragment.PREMIUM_FEATURE_ADS, true).show();
                        }"""
    new = """if (UserConfig.getInstance(currentAccount).isPremium()) {
                            fragment.getMessagesController().disableAds(true);
                            removeAllAds();
                            BulletinFactory.of(fragment)
                                .createAdReportedBulletin(LocaleController.getString(R.string.AdHidden))
                                .show();
                        } else if (TeleBetaFreemium.hasAllAccess(currentAccount)) {
                            removeAllAds();
                            BulletinFactory.of(fragment)
                                .createAdReportedBulletin(LocaleController.getString(R.string.AdHidden))
                                .show();
                        } else {
                            new PremiumFeatureBottomSheet(fragment, PremiumPreviewFragment.PREMIUM_FEATURE_ADS, true).show();
                        }"""
    if source.count(old) == 1:
        source = source.replace(old, new, 1)
    elif source.count(new) == 1:
        pass
    else:
        raise RuntimeError("SearchViewPager Remove Ads action anchor mismatch")
    return patch_local_premium_checks(source, ())
