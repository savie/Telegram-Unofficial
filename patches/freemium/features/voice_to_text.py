"""Voice-to-Text Conversion: buka gate client-side pada tombol dan jalur transkripsi."""
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = ("ui/Components/TranscribeButton.java",)


def patch_transcribe_button(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(parent.getMessageObject().currentAccount).isPremium()",
         "TeleBetaFreemium.hasAllAccess(parent.getMessageObject().currentAccount)", 1),
        ("UserConfig.getInstance(account).isPremium()",
         "TeleBetaFreemium.hasAllAccess(account)", 1),
        ("UserConfig.getInstance(messageObject.currentAccount).isPremium()",
         "TeleBetaFreemium.hasAllAccess(messageObject.currentAccount)", 1),
    ))
