"""Telegram Business: validasi source upstream untuk seluruh delapan subfitur."""
from ..integration.business_feature_gates import BUSINESS_GATE_TARGETS, BUSINESS_SOURCE_FILES
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = BUSINESS_SOURCE_FILES + ("ui/Components/ChatGreetingsView.java",)

# Seluruh operasi tetap memakai controller dan request Telegram upstream.
# Gate lokal membuka entry point; keputusan server tetap menjadi otoritas operasi.
SERVER_BACKED_FEATURES = tuple(BUSINESS_GATE_TARGETS)



def patch_chat_greetings_view(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("if (premiumLock) {", "if (premiumLock && !TeleBetaFreemium.hasAllAccess(currentAccount)) {", 2),
        (
            "final boolean premiumLocked = MessagesController.getInstance(currentAccount).premiumFeaturesBlocked();",
            "final boolean premiumLocked = MessagesController.getInstance(currentAccount).premiumFeaturesBlocked() && !TeleBetaFreemium.hasAllAccess(currentAccount);",
            2,
        ),
    ))


def patch_quick_replies_layout(source: str) -> str:
    """Buka gate pemanggilan Quick Replies Business tanpa mengganti UI/controller upstream."""
    source = patch_local_premium_checks(source, (
        ("if (!UserConfig.getInstance(parentAlert.currentAccount).isPremium()) {",
         "if (!TeleBetaFreemium.hasAllAccess(parentAlert.currentAccount)) {", 1),
    ))
    old_account = "QuickRepliesController.getInstance(UserConfig.selectedAccount).sendQuickReplyTo("
    new_account = "QuickRepliesController.getInstance(parentAlert.currentAccount).sendQuickReplyTo("
    if source.count(old_account) == 1:
        source = source.replace(old_account, new_account, 1)
    elif source.count(old_account) != 0 or source.count(new_account) != 1:
        raise RuntimeError("Quick Replies send action account context anchor mismatch")
    return source
