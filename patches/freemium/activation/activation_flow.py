"""Pengalihan purchase Telegram ke aktivasi lokal Freemium V2."""

PURCHASE_METHOD_SIGNATURE = (
    "public static void buyPremium(BaseFragment fragment, SubscriptionTier tier, "
    "String source, boolean forcePremium, "
    "BillingFlowParams.SubscriptionUpdateParams updateParams) {"
)
NEXT_METHOD_MARKER = "    public static String getPremiumButtonText("
USER_CONFIG_IMPORT = "import org.telegram.messenger.UserConfig;"
FREEMIUM_IMPORT = "import org.telegram.messenger.TeleBetaFreemium;"


def patch_purchase_flow(source: str) -> str:
    """Ganti hanya implementasi purchase entry point; UI dan nama method tetap."""
    if source.count(PURCHASE_METHOD_SIGNATURE) != 1:
        raise RuntimeError("Premium purchase method anchor must exist exactly once")
    if source.count(NEXT_METHOD_MARKER) != 1:
        raise RuntimeError("Premium button method boundary must exist exactly once")
    if source.count(USER_CONFIG_IMPORT) != 1:
        raise RuntimeError("UserConfig import anchor must exist exactly once")

    start = source.index(PURCHASE_METHOD_SIGNATURE)
    end = source.index(NEXT_METHOD_MARKER, start)
    current_method = source[start:end]
    if "TeleBetaFreemium.activate(account)" in current_method:
        patched = source
    else:
        replacement = '''public static void buyPremium(BaseFragment fragment, SubscriptionTier tier, String source, boolean forcePremium, BillingFlowParams.SubscriptionUpdateParams updateParams) {
        final int account = fragment == null ? UserConfig.selectedAccount : fragment.getCurrentAccount();
        if (!UserConfig.isValidAccount(account)) {
            return;
        }
        if (!TeleBetaFreemium.activate(account)) {
            return;
        }
        if (fragment instanceof PremiumPreviewFragment) {
            PremiumPreviewFragment preview = (PremiumPreviewFragment) fragment;
            preview.forcePremium = true;
            preview.updateRows();
        }
    }

'''
        patched = source[:start] + replacement + source[end:]

    if FREEMIUM_IMPORT not in patched:
        patched = patched.replace(
            USER_CONFIG_IMPORT,
            USER_CONFIG_IMPORT + "\n" + FREEMIUM_IMPORT,
            1,
        )

    # PremiumPreviewFragment owns the Premium/Business preview gates. Keep
    # Telegram's user.premium state untouched; consult local entitlement only
    # for these client-side entry points and presentation decisions.
    patched = patched.replace(
        "getUserConfig().isPremium()",
        "TeleBetaFreemium.hasAllAccess(currentAccount)"
    )
    patched = patched.replace(
        "UserConfig.getInstance(currentAccount).isPremium()",
        "TeleBetaFreemium.hasAllAccess(currentAccount)"
    )
    return patched
