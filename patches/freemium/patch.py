#!/usr/bin/env python3
"""Penerapan inti Tele-ß Freemium V2 pada source Telegram yang telah divendorkan."""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
UPSTREAM_ROOT = REPO_ROOT / "upstream"
JAVA_ROOT = UPSTREAM_ROOT / "TMessagesProj/src/main/java/org/telegram/messenger"
PREMIUM_PREVIEW = UPSTREAM_ROOT / "TMessagesProj/src/main/java/org/telegram/ui/PremiumPreviewFragment.java"

CORE_SOURCE = r"""package org.telegram.messenger;

import android.content.Context;
import android.content.SharedPreferences;

/**
 * Entitlement Freemium lokal Tele-ß.
 *
 * Status disimpan per identitas akun Telegram (clientUserId), bukan indeks slot
 * akun Telegram. Class ini tidak mengubah status Premium atau Business server.
 */
public final class TeleBetaFreemium {
    private static final String PREFS_PREFIX = "telebeta_freemium_v2_";
    private static final String KEY_ACTIVE = "all_access_active";
    private static final int SCHEMA_VERSION = 2;

    // Katalog produk V2: satu entitlement memberikan akses ke seluruh katalog.
    public static final String[] PREMIUM_CATALOG = {
            "stories", "unlimited_cloud_storage", "doubled_limits", "telegram_business",
            "last_seen_times", "voice_to_text", "faster_download_speed", "real_time_translation",
            "animated_emoji", "emoji_statuses", "saved_message_tags", "name_profile_colors",
            "two_sided_wallpaper", "profile_badge", "paid_messages", "disable_sharing",
            "advanced_chat_management", "no_ads", "premium_app_icons", "infinite_reactions",
            "animated_profile_pictures", "premium_stickers", "message_effects", "ai_tools",
            "formatting_tools", "checklists"
    };

    public static final String[] BUSINESS_CATALOG = {
            "location", "opening_hours", "quick_replies", "greeting_messages",
            "away_messages", "chat_links", "start_page", "chatbots"
    };

    private TeleBetaFreemium() {
    }

    private static SharedPreferences preferences(int account) {
        if (account < 0 || account >= UserConfig.MAX_ACCOUNT_COUNT) {
            throw new IllegalArgumentException("Invalid Telegram account slot: " + account);
        }
        long clientUserId = UserConfig.getInstance(account).getClientUserId();
        if (clientUserId <= 0L) {
            throw new IllegalStateException("Freemium requires an authenticated Telegram account.");
        }
        Context context = ApplicationLoader.applicationContext;
        if (context == null) {
            throw new IllegalStateException("Application context is not initialized.");
        }
        return context.getSharedPreferences(PREFS_PREFIX + clientUserId, Context.MODE_PRIVATE);
    }

    public static boolean isActive(int account) {
        try {
            SharedPreferences prefs = preferences(account);
            return prefs.getInt("schema_version", SCHEMA_VERSION) == SCHEMA_VERSION
                    && prefs.getBoolean(KEY_ACTIVE, false);
        } catch (IllegalStateException | IllegalArgumentException error) {
            return false;
        }
    }

    public static void activate(int account) {
        SharedPreferences prefs = preferences(account);
        prefs.edit()
                .putInt("schema_version", SCHEMA_VERSION)
                .putBoolean(KEY_ACTIVE, true)
                .apply();
    }

    public static boolean redirectPurchaseToFreemium(int account) {
        activate(account);
        return true;
    }

    /**
     * Semua kategori dan subfitur menggunakan entitlement All-access yang sama.
     * Feature ID hanya mengidentifikasi jalur implementasi, bukan hak akses terpisah.
     */
    public static boolean hasAccess(int account, String featureId) {
        return featureId != null && !featureId.isEmpty() && isActive(account);
    }

    public static boolean hasBusinessAccess(int account, String businessFeatureId) {
        return businessFeatureId != null && !businessFeatureId.isEmpty() && isActive(account);
    }

    public static void deactivate(int account) {
        SharedPreferences prefs = preferences(account);
        prefs.edit()
                .putInt("schema_version", SCHEMA_VERSION)
                .putBoolean(KEY_ACTIVE, false)
                .apply();
    }
}
"""

def write_core() -> None:
    JAVA_ROOT.mkdir(parents=True, exist_ok=True)
    target = JAVA_ROOT / "TeleBetaFreemium.java"
    target.write_text(CORE_SOURCE, encoding="utf-8")

def patch_premium_activation() -> None:
    source = PREMIUM_PREVIEW.read_text(encoding="utf-8")
    import_anchor = "import org.telegram.messenger.UserConfig;"
    if "import org.telegram.messenger.TeleBetaFreemium;" not in source:
        if import_anchor not in source:
            raise SystemExit("PremiumPreviewFragment import anchor not found.")
        source = source.replace(
            import_anchor,
            "import org.telegram.messenger.TeleBetaFreemium;\n" + import_anchor,
            1,
        )

    method_start = source.find("    private void updateButtonText(boolean animated) {")
    method_end = source.find("    @Override\n    public boolean isLightStatusBar()", method_start)
    if method_start < 0 or method_end < 0:
        raise SystemExit("PremiumPreviewFragment updateButtonText method boundaries changed.")
    method_replacement = """    private void updateButtonText(boolean animated) {
        if (premiumButtonView == null) {
            return;
        }
        boolean active = TeleBetaFreemium.isActive(currentAccount);
        premiumButtonView.setButton(active ? "Freemium Aktif" : "Aktifkan Freemium", null, animated);
        buttonContainerInternal.setOnClickListener(v -> {
            if (TeleBetaFreemium.isActive(currentAccount)) {
                return;
            }
            try {
                TeleBetaFreemium.activate(currentAccount);
                updateButtonText(true);
                android.widget.Toast.makeText(getContext(), "Freemium berhasil diaktifkan.", android.widget.Toast.LENGTH_SHORT).show();
            } catch (IllegalStateException error) {
                android.widget.Toast.makeText(getContext(), "Akun Telegram belum siap untuk mengaktifkan Freemium.", android.widget.Toast.LENGTH_LONG).show();
            }
        });
    }

"""
    source = source[:method_start] + method_replacement + source[method_end:]

    purchase_start = source.find("    public static void buyPremium(BaseFragment fragment, SubscriptionTier tier, String source, boolean forcePremium, BillingFlowParams.SubscriptionUpdateParams updateParams) {")
    purchase_end = source.find("    public static void fillPremiumFeaturesList", purchase_start)
    if purchase_start < 0 or purchase_end < 0:
        raise SystemExit("Premium purchase method boundaries changed.")
    purchase_method = source[purchase_start:purchase_end]
    purchase_lines = purchase_method.splitlines(keepends=True)
    account_lines = [line for line in purchase_lines if line.strip().startswith("final int account = fragment == null ? UserConfig.selectedAccount")]
    if len(account_lines) != 1:
        raise SystemExit("Premium purchase account resolution changed.")
    purchase_method = "".join(line for line in purchase_lines if line not in account_lines)
    signature_end = purchase_method.find("{")
    if signature_end < 0:
        raise SystemExit("Premium purchase method signature changed.")
    redirect = """\n        final int account = fragment == null ? UserConfig.selectedAccount : fragment.getCurrentAccount();
        if (account >= 0) {
            try {
                TeleBetaFreemium.activate(account);
                android.content.Context toastContext = fragment != null ? fragment.getParentActivity() : LaunchActivity.instance;
                if (toastContext != null) {
                    android.widget.Toast.makeText(toastContext, "Freemium berhasil diaktifkan untuk akun ini.", android.widget.Toast.LENGTH_SHORT).show();
                }
                return;
            } catch (IllegalStateException error) {
                android.content.Context toastContext = fragment != null ? fragment.getParentActivity() : LaunchActivity.instance;
                if (toastContext != null) {
                    android.widget.Toast.makeText(toastContext, "Akun Telegram belum siap untuk mengaktifkan Freemium.", android.widget.Toast.LENGTH_LONG).show();
                }
                return;
            }
        }
"""
    purchase_method = purchase_method[:signature_end + 1] + redirect + purchase_method[signature_end + 1:]
    source = source[:purchase_start] + purchase_method + source[purchase_end:]
    click_gate = "if (type == FEATURES_BUSINESS && getUserConfig().isPremium()) {"
    click_gate_local = "if (type == FEATURES_BUSINESS && (getUserConfig().isPremium() || TeleBetaFreemium.hasBusinessAccess(currentAccount, \"telegram_business\"))) {"
    if source.count(click_gate) != 1:
        raise SystemExit("PremiumPreviewFragment Business navigation gate changed.")
    source = source.replace(click_gate, click_gate_local, 1)

    PREMIUM_PREVIEW.write_text(source, encoding="utf-8")

def patch_feature_gates() -> None:
    """Hubungkan gate UI yang sudah terpetakan ke entitlement All-access V2."""
    replacements = {
        "TMessagesProj/src/main/java/org/telegram/ui/Components/SearchTagsList.java": [
            ("!UserConfig.getInstance(currentAccount).isPremium()", "!UserConfig.getInstance(currentAccount).isPremium() && !TeleBetaFreemium.hasAccess(currentAccount, \"saved_message_tags\")"),
        ],
        "TMessagesProj/src/main/java/org/telegram/ui/Components/TranslateButton.java": [
            ("UserConfig.getInstance(currentAccount).isPremium()", "(UserConfig.getInstance(currentAccount).isPremium() || TeleBetaFreemium.hasAccess(currentAccount, \"real_time_translation\"))"),
        ],
        "TMessagesProj/src/main/java/org/telegram/ui/Components/TranslateAlert3.java": [
            ("!UserConfig.getInstance(currentAccount).isPremium()", "!UserConfig.getInstance(currentAccount).isPremium() && !TeleBetaFreemium.hasAccess(currentAccount, \"real_time_translation\")"),
        ],
        "TMessagesProj/src/main/java/org/telegram/ui/iv/RichEditor.java": [
            ("!MessagesController.getInstance(currentAccount).richEditorAllowed() && !UserConfig.getInstance(currentAccount).isPremium()", "!MessagesController.getInstance(currentAccount).richEditorAllowed() && !UserConfig.getInstance(currentAccount).isPremium() && !TeleBetaFreemium.hasAccess(currentAccount, \"formatting_tools\")"),
            ("if (!UserConfig.getInstance(currentAccount).isPremium())", "if (!UserConfig.getInstance(currentAccount).isPremium() && !TeleBetaFreemium.hasAccess(currentAccount, \"formatting_tools\"))"),
        ],
        "TMessagesProj/src/main/java/org/telegram/ui/iv/ChatAttachAlertRichLayout.java": [
            ("!MessagesController.getInstance(currentAccount).richEditorAllowed() && !UserConfig.getInstance(currentAccount).isPremium()", "!MessagesController.getInstance(currentAccount).richEditorAllowed() && !UserConfig.getInstance(currentAccount).isPremium() && !TeleBetaFreemium.hasAccess(currentAccount, \"formatting_tools\")"),
            ("!UserConfig.getInstance(currentAccount).isPremium()", "!UserConfig.getInstance(currentAccount).isPremium() && !TeleBetaFreemium.hasAccess(currentAccount, \"formatting_tools\")"),
        ],

        "TMessagesProj/src/main/java/org/telegram/ui/Components/StickersAlert.java": [
            ("!UserConfig.getInstance(currentAccount).isPremium()", "!UserConfig.getInstance(currentAccount).isPremium() && !TeleBetaFreemium.hasAccess(currentAccount, \"premium_stickers\")"),
        ],
        "TMessagesProj/src/main/java/org/telegram/ui/Components/EmojiPacksAlert.java": [
            ("!UserConfig.getInstance(currentAccount).isPremium()", "!UserConfig.getInstance(currentAccount).isPremium() && !TeleBetaFreemium.hasAccess(currentAccount, \"premium_stickers\")"),
        ],
        "TMessagesProj/src/main/java/org/telegram/ui/SelectAnimatedEmojiDialog.java": [
            ("!UserConfig.getInstance(currentAccount).isPremium()", "!UserConfig.getInstance(currentAccount).isPremium() && !TeleBetaFreemium.hasAccess(currentAccount, \"animated_emoji\")"),
            ("UserConfig.getInstance(currentAccount).isPremium()", "(UserConfig.getInstance(currentAccount).isPremium() || TeleBetaFreemium.hasAccess(currentAccount, \"animated_emoji\"))"),
        ],
        "TMessagesProj/src/main/java/org/telegram/ui/Components/SuggestEmojiView.java": [
            ("SharedConfig.suggestAnimatedEmoji && UserConfig.getInstance(currentAccount).isPremium()", "SharedConfig.suggestAnimatedEmoji && (UserConfig.getInstance(currentAccount).isPremium() || TeleBetaFreemium.hasAccess(currentAccount, \"animated_emoji\"))"),
        ],
        "TMessagesProj/src/main/java/org/telegram/ui/Adapters/StickersAdapter.java": [
            ("SharedConfig.suggestAnimatedEmoji && UserConfig.getInstance(currentAccount).isPremium()", "SharedConfig.suggestAnimatedEmoji && (UserConfig.getInstance(currentAccount).isPremium() || TeleBetaFreemium.hasAccess(currentAccount, \"animated_emoji\"))"),
        ], 
        "TMessagesProj/src/main/java/org/telegram/ui/Business/ChatAttachAlertQuickRepliesLayout.java": [
            ("!UserConfig.getInstance(parentAlert.currentAccount).isPremium()", "!UserConfig.getInstance(parentAlert.currentAccount).isPremium() && !TeleBetaFreemium.hasBusinessAccess(parentAlert.currentAccount, \"quick_replies\")"),
        ],   }

    for relative_path, pairs in replacements.items():
        path = UPSTREAM_ROOT / relative_path
        if not path.is_file():
            raise SystemExit(f"Freemium V2 feature source is missing: {relative_path}")
        source = path.read_text(encoding="utf-8")
        original = source
        for old, new in pairs:
            source = source.replace(old, new)
        if source == original:
            raise SystemExit(f"No expected Freemium V2 gate found in {relative_path}")
        import_line = "import org.telegram.messenger.TeleBetaFreemium;\n"
        if "import org.telegram.messenger.TeleBetaFreemium;" not in source:
            package_line = next((line for line in source.splitlines(keepends=True) if line.startswith("package ")), None)
            if package_line is None:
                raise SystemExit(f"Java package declaration missing: {relative_path}")
            source = source.replace(package_line, package_line + "\n" + import_line, 1)
        path.write_text(source, encoding="utf-8")


def apply_freemium() -> None:
    if not (UPSTREAM_ROOT / "TMessagesProj/src/main/java/org/telegram/messenger/UserConfig.java").is_file():
        raise SystemExit("UserConfig.java is missing from upstream source.")
    if not PREMIUM_PREVIEW.is_file():
        raise SystemExit("PremiumPreviewFragment.java is missing from upstream source.")
    write_core()
    patch_premium_activation()
    patch_feature_gates()

if __name__ == "__main__":
    apply_freemium()
