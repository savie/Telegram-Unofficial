"""Faster Download Speed: buka budget client-side tanpa membuat download manager pengganti."""
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = ("messenger/FileLoadOperation.java",)


def patch_file_load_operation(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 1),
    ))
