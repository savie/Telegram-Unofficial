"""Doubled Limits dan ukuran upload: buka batas client-side, server tetap authoritative."""
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = (
    "ui/ChatRightsEditActivity.java",
    "ui/SelectChatUserSheet.java",
    "ui/Components/ChatAttachAlertDocumentLayout.java",
    "ui/Components/PhotoViewerCaptionEnterView.java",
    "messenger/FileUploadOperation.java",
)


def patch_chat_rights_edit_activity(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("!AccountInstance.getInstance(currentAccount).getUserConfig().isPremium()", "!TeleBetaFreemium.hasAllAccess(currentAccount)", 1),
    ))


def patch_select_chat_user_sheet(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("!AccountInstance.getInstance(currentAccount).getUserConfig().isPremium()", "!TeleBetaFreemium.hasAllAccess(currentAccount)", 1),
    ))


def patch_document_layout(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("!UserConfig.getInstance(UserConfig.selectedAccount).isPremium()", "!TeleBetaFreemium.hasAllAccess(UserConfig.selectedAccount)", 1),
    ))


def patch_photo_viewer_caption(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("!UserConfig.getInstance(currentAccount).isPremium()", "!TeleBetaFreemium.hasAllAccess(currentAccount)", 1),
    ))



def patch_file_upload_operation(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("AccountInstance.getInstance(currentAccount).getUserConfig().isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 2),
    ))
