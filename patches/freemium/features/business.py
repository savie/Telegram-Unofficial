"""Telegram Business: gate lokal untuk seluruh delapan subfitur."""
from ..integration.business_feature_gates import BUSINESS_GATE_TARGETS, BUSINESS_SOURCE_FILES
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = BUSINESS_SOURCE_FILES + ("ui/Components/ChatGreetingsView.java",)

# Seluruh operasi tetap memakai controller dan request Telegram upstream.
# Gate lokal membuka entry point; keputusan server tetap menjadi otoritas operasi.
SERVER_BACKED_FEATURES = tuple(BUSINESS_GATE_TARGETS)



def patch_business_activity_gate(source: str) -> str:
    """Buka layar Business untuk entitlement lokal tanpa mengubah request/server API."""
    import re

    if "import org.telegram.messenger.TeleBetaFreemium;" not in source:
        anchor = "import org.telegram."
        if source.count(anchor) < 1:
            raise RuntimeError("Business activity import anchor missing")
        source = source.replace(anchor, "import org.telegram.messenger.TeleBetaFreemium;\n" + anchor, 1)

    guard = "if (getMessagesController().premiumFeaturesBlocked() && !TeleBetaFreemium.hasAllAccess(currentAccount)) {\n            return false;\n        }"
    method = re.search(r"(?m)^\s*(?:public|protected) boolean onFragmentCreate\(\)\s*\{", source)
    if method:
        body_start = method.end()
        if guard in source:
            return source
        source = source[:body_start] + "\n        " + guard + source[body_start:]
        return source

    class_match = re.search(r"(?m)^public class [^{]+\{", source)
    if not class_match:
        raise RuntimeError("Business activity class declaration missing")
    method_source = (
        "\n    @Override\n"
        "    public boolean onFragmentCreate() {\n"
        "        " + guard + "\n"
        "        return super.onFragmentCreate();\n"
        "    }\n"
    )
    return source[:class_match.end()] + method_source + source[class_match.end():]


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
