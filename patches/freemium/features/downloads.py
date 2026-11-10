"""Faster Download Speed: buka budget client-side tanpa membuat download manager pengganti."""
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = ("messenger/FileLoader.java", "messenger/FileLoadOperation.java")


def patch_file_loader(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("AccountInstance.getInstance(currentAccount).getUserConfig().isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 1),
    ))


def patch_file_load_operation(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 1),
    ))
