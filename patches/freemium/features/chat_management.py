"""Advanced Chat Management: batas folder, pin, dan Saved Messages."""
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = ("ui/DialogsActivity.java", "messenger/SavedMessagesController.java")


def patch_saved_messages_controller(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 2),
    ))


def patch_dialogs_activity(source: str) -> str:
    return patch_local_premium_checks(source, (
        (
            "totalCount > getMessagesController().dialogFiltersChatsLimitDefault && !getUserConfig().isPremium()",
            "totalCount > getMessagesController().dialogFiltersChatsLimitDefault && !TeleBetaFreemium.hasAllAccess(currentAccount)",
            1,
        ),
        (
            "if (getUserConfig().isPremium()) {\\n                    maxPinnedCount = getMessagesController().maxFolderPinnedDialogsCountPremium;",
            "if (TeleBetaFreemium.hasAllAccess(currentAccount)) {\\n                    maxPinnedCount = getMessagesController().maxFolderPinnedDialogsCountPremium;",
            1,
        ),
        (
            "if (getUserConfig().isPremium()) {\\n                    maxPinnedCount = getMessagesController().maxPinnedDialogsCountPremium;",
            "if (TeleBetaFreemium.hasAllAccess(currentAccount)) {\\n                    maxPinnedCount = getMessagesController().maxPinnedDialogsCountPremium;",
            1,
        ),
        (
            "if (UserConfig.getInstance(currentAccount).isPremium()) {\\n                    maxPinnedCount = getMessagesController().maxFolderPinnedDialogsCountPremium;",
            "if (TeleBetaFreemium.hasAllAccess(currentAccount)) {\\n                    maxPinnedCount = getMessagesController().maxFolderPinnedDialogsCountPremium;",
            1,
        ),
        (
            "getUserConfig().isPremium() ? getMessagesController().dialogFiltersPinnedLimitPremium : getMessagesController().dialogFiltersPinnedLimitDefault",
            "TeleBetaFreemium.hasAllAccess(currentAccount) ? getMessagesController().dialogFiltersPinnedLimitPremium : getMessagesController().dialogFiltersPinnedLimitDefault",
            1,
        ),
        (
            "!getUserConfig().isPremium() && !getMessagesController().premiumFeaturesBlocked() && visibleByDownload && visibleByPosition",
            "!TeleBetaFreemium.hasAllAccess(currentAccount) && !getMessagesController().premiumFeaturesBlocked() && visibleByDownload && visibleByPosition",
            1,
        ),
    ))
