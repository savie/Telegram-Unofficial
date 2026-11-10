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
