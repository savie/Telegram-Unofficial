"""Advanced Chat Management: folder limits, tags, archive, pin, dan Saved Messages."""
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = (
    "ui/DialogsActivity.java",
    "ui/ArchiveSettingsActivity.java",
    "ui/FiltersSetupActivity.java",
    "ui/FilterCreateActivity.java",
    "ui/FilterChatlistActivity.java",
    "ui/Components/DialogCellTags.java",
    "messenger/SavedMessagesController.java",
)


def patch_saved_messages_controller(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 2),
    ))


def patch_dialogs_activity(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("totalCount > getMessagesController().dialogFiltersChatsLimitDefault && !getUserConfig().isPremium()",
         "totalCount > getMessagesController().dialogFiltersChatsLimitDefault && !TeleBetaFreemium.hasAllAccess(currentAccount)", 1),
        ("if (getUserConfig().isPremium()) {\n                    maxPinnedCount = getMessagesController().maxFolderPinnedDialogsCountPremium;",
         "if (TeleBetaFreemium.hasAllAccess(currentAccount)) {\n                    maxPinnedCount = getMessagesController().maxFolderPinnedDialogsCountPremium;", 1),
        ("if (getUserConfig().isPremium()) {\n                    maxPinnedCount = getMessagesController().maxPinnedDialogsCountPremium;",
         "if (TeleBetaFreemium.hasAllAccess(currentAccount)) {\n                    maxPinnedCount = getMessagesController().maxPinnedDialogsCountPremium;", 1),
        ("if (UserConfig.getInstance(currentAccount).isPremium()) {\n                    maxPinnedCount = getMessagesController().maxFolderPinnedDialogsCountPremium;",
         "if (TeleBetaFreemium.hasAllAccess(currentAccount)) {\n                    maxPinnedCount = getMessagesController().maxFolderPinnedDialogsCountPremium;", 1),
        ("getUserConfig().isPremium() ? getMessagesController().dialogFiltersPinnedLimitPremium : getMessagesController().dialogFiltersPinnedLimitDefault",
         "TeleBetaFreemium.hasAllAccess(currentAccount) ? getMessagesController().dialogFiltersPinnedLimitPremium : getMessagesController().dialogFiltersPinnedLimitDefault", 1),
        ("!getUserConfig().isPremium() && !getMessagesController().premiumFeaturesBlocked() && visibleByDownload && visibleByPosition",
         "!TeleBetaFreemium.hasAllAccess(currentAccount) && !getMessagesController().premiumFeaturesBlocked() && visibleByDownload && visibleByPosition", 1),
    ))


def patch_archive_settings(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("!getUserConfig().isPremium()", "!TeleBetaFreemium.hasAllAccess(currentAccount)", 2),
    ))


def patch_filters_setup(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("getUserConfig().isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 4),
        ("UserConfig.getInstance(UserConfig.selectedAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 1),
    ))


def patch_filter_create(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("getUserConfig().isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 9),
    ))


def patch_filter_chatlist(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("getUserConfig().isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 1),
    ))


def patch_dialog_cell_tags(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("account.getUserConfig().isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 1),
    ))
