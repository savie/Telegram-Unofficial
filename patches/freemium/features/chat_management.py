"""Advanced Chat Management: folder limits, tags, archive, pin, dan Saved Messages."""
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = (
    "ui/ChatActivity.java",
    "ui/DialogsActivity.java",
    "ui/ArchiveSettingsActivity.java",
    "ui/FiltersSetupActivity.java",
    "ui/FilterCreateActivity.java",
    "ui/FilterChatlistActivity.java",
    "ui/Components/DialogCellTags.java",
    "ui/Components/FilterTabsView.java",
    "ui/UsersSelectActivity.java",
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
        ("!getUserConfig().isPremium()", "!TeleBetaFreemium.hasAllAccess(getCurrentAccount())", 1),
        ("getUserConfig().isPremium() || getMessagesController().autoarchiveAvailable",
         "TeleBetaFreemium.hasAllAccess(getCurrentAccount()) || getMessagesController().autoarchiveAvailable", 1),
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

def patch_filter_tabs_view(source: str) -> str:
    return patch_local_premium_checks(source, (
        (
            "MessagesController.getInstance(UserConfig.selectedAccount).premiumFeaturesBlocked() && (!isEditing || (viewHolder.getAdapterPosition() == 0 && tabs.get(0).isDefault && !UserConfig.getInstance(UserConfig.selectedAccount).isPremium()))",
            "MessagesController.getInstance(UserConfig.selectedAccount).premiumFeaturesBlocked() && !TeleBetaFreemium.hasAllAccess(UserConfig.selectedAccount) && (!isEditing || (viewHolder.getAdapterPosition() == 0 && tabs.get(0).isDefault && !TeleBetaFreemium.hasAllAccess(UserConfig.selectedAccount)))",
            1,
        ),
        (
            "MessagesController.getInstance(UserConfig.selectedAccount).premiumFeaturesBlocked() && ((source.getAdapterPosition() == 0 || target.getAdapterPosition() == 0) && !UserConfig.getInstance(UserConfig.selectedAccount).isPremium())",
            "MessagesController.getInstance(UserConfig.selectedAccount).premiumFeaturesBlocked() && !TeleBetaFreemium.hasAllAccess(UserConfig.selectedAccount) && ((source.getAdapterPosition() == 0 || target.getAdapterPosition() == 0) && !TeleBetaFreemium.hasAllAccess(UserConfig.selectedAccount))",
            1,
        ),
        (
            "UserConfig.getInstance(UserConfig.selectedAccount).isPremium()",
            "TeleBetaFreemium.hasAllAccess(UserConfig.selectedAccount)",
            1,
        ),
    ))



def patch_chat_activity_saved_message_tags(source: str) -> str:
    replacements = (
        (
            "actionMode.setItemVisibility(tag_message, getUserConfig().isPremium() ? View.VISIBLE : View.GONE);",
            "actionMode.setItemVisibility(tag_message, TeleBetaFreemium.hasAllAccess(currentAccount) ? View.VISIBLE : View.GONE);",
            1,
        ),
        (
            "tagItem.setVisibility(getUserConfig().isPremium() && (",
            "tagItem.setVisibility(TeleBetaFreemium.hasAllAccess(currentAccount) && (",
            1,
        ),
        (
            "if (getDialogId() != getUserConfig().getClientUserId() || !getUserConfig().isPremium()) return;",
            "if (getDialogId() != getUserConfig().getClientUserId() || !TeleBetaFreemium.hasAllAccess(currentAccount)) return;",
            1,
        ),
        (
            "&& getUserConfig().isPremium();",
            "&& TeleBetaFreemium.hasAllAccess(currentAccount);",
            1,
        ),
        (
            "if (getUserConfig().isPremium()) {\n                savedMessagesTagHint = new HintView2",
            "if (TeleBetaFreemium.hasAllAccess(currentAccount)) {\n                savedMessagesTagHint = new HintView2",
            1,
        ),
        (
            "if (getDialogId() == getUserConfig().getClientUserId() && !getUserConfig().isPremium()) {",
            "if (getDialogId() == getUserConfig().getClientUserId() && !TeleBetaFreemium.hasAllAccess(currentAccount)) {",
            1,
        ),
        (
            "getUserConfig().isPremium() ? LocaleController.getString(R.string.SavedTagReactionsHint2)",
            "TeleBetaFreemium.hasAllAccess(currentAccount) ? LocaleController.getString(R.string.SavedTagReactionsHint2)",
            1,
        ),
        (
            "if (getDialogId() == getUserConfig().getClientUserId() && !getUserConfig().isPremium() && primaryMessage.messageOwner != null && (primaryMessage.messageOwner.reactions == null || (primaryMessage.messageOwner.reactions.reactions_as_tags || primaryMessage.messageOwner.reactions.results.isEmpty()))) {",
            "if (getDialogId() == getUserConfig().getClientUserId() && !TeleBetaFreemium.hasAllAccess(currentAccount) && primaryMessage.messageOwner != null && (primaryMessage.messageOwner.reactions == null || (primaryMessage.messageOwner.reactions.reactions_as_tags || primaryMessage.messageOwner.reactions.results.isEmpty()))) {",
            1,
        ),
        (
            "getUserConfig().getClientUserId() == getDialogId() && messageObject.areTags() && !getUserConfig().isPremium()",
            "getUserConfig().getClientUserId() == getDialogId() && messageObject.areTags() && !TeleBetaFreemium.hasAllAccess(currentAccount)",
            1,
        ),
        (
            "if (getUserConfig().isPremium()) {\n                    ActionBarMenuSubItem editTag =",
            "if (TeleBetaFreemium.hasAllAccess(currentAccount)) {\n                    ActionBarMenuSubItem editTag =",
            1,
        ),
    )

    # Sepuluh anchor wajib: original tepat satu kali atau replacement tepat satu kali.
    # Anchor hilang, duplikat, dan kondisi campuran harus gagal sebelum transformasi.
    if len(replacements) != 10:
        raise RuntimeError("ChatActivity Saved Messages Tags requires exactly 10 anchors")

    for old, new, expected_count in replacements:
        old_count = source.count(old)
        new_count = source.count(new)

        original_state = old_count == expected_count and new_count == 0
        patched_state = old_count == 0 and new_count == expected_count

        if not (original_state or patched_state):
            raise RuntimeError(
                "ChatActivity Saved Messages Tags anchor mismatch: "
                f"expected original={expected_count}, replacement={expected_count}; "
                f"found original={old_count}, replacement={new_count}; "
                f"anchor={old!r}"
            )

    return patch_local_premium_checks(source, replacements)


def patch_users_select_activity(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("getUserConfig().isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 2),
    ))
