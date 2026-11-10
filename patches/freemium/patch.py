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

    method_anchor = """    private void updateButtonText(boolean animated) {
        if (premiumButtonView == null) {
            return;
        }"""
    replacement = """    private void updateButtonText(boolean animated) {
        if (premiumButtonView == null) {
            return;
        }
        // Tele-ß grants one local all-access entitlement; Telegram billing is not invoked.
        if (TeleBetaFreemium.isActive(currentAccount)) {
            premiumButtonView.setButton("Freemium Aktif", null, animated);
            buttonContainerInternal.setOnClickListener(v -> {
                android.widget.Toast.makeText(getContext(), "Semua fitur Freemium sudah aktif untuk akun ini.", android.widget.Toast.LENGTH_SHORT).show();
            });
            return;
        }
        premiumButtonView.setButton("Aktifkan Freemium", null, animated);
        buttonContainerInternal.setOnClickListener(v -> {
            try {
                TeleBetaFreemium.activate(currentAccount);
                updateButtonText(true);
                android.widget.Toast.makeText(getContext(), "Freemium berhasil diaktifkan.", android.widget.Toast.LENGTH_SHORT).show();
            } catch (IllegalStateException error) {
                android.widget.Toast.makeText(getContext(), "Akun Telegram belum siap untuk mengaktifkan Freemium.", android.widget.Toast.LENGTH_LONG).show();
            }
        });
        return;"""
    if replacement not in source:
        if method_anchor not in source:
            raise SystemExit("PremiumPreviewFragment updateButtonText anchor not found.")
        source = source.replace(method_anchor, replacement, 1)
    elif "TeleBetaFreemium.isActive(currentAccount)" not in source:
        raise SystemExit("Unexpected PremiumPreviewFragment patch state.")
    purchase_anchor = """    public static void buyPremium(BaseFragment fragment, SubscriptionTier tier, String source, boolean forcePremium, BillingFlowParams.SubscriptionUpdateParams updateParams) {
        if (BuildVars.IS_BILLING_UNAVAILABLE) {"""
    purchase_replacement = """    public static void buyPremium(BaseFragment fragment, SubscriptionTier tier, String source, boolean forcePremium, BillingFlowParams.SubscriptionUpdateParams updateParams) {
        final int account = fragment == null ? UserConfig.selectedAccount : fragment.getCurrentAccount();
        if (TeleBetaFreemium.redirectPurchaseToFreemium(account)) {
            android.content.Context toastContext = fragment != null ? fragment.getParentActivity() : LaunchActivity.instance;
            if (toastContext != null) {
                android.widget.Toast.makeText(toastContext, "Freemium berhasil diaktifkan untuk akun ini.", android.widget.Toast.LENGTH_SHORT).show();
            }
            return;
        }
        if (BuildVars.IS_BILLING_UNAVAILABLE) {"""
    if purchase_replacement not in source:
        if purchase_anchor not in source:
            raise SystemExit("Premium purchase entry point anchor not found.")
        source = source.replace(purchase_anchor, purchase_replacement, 1)
        account_line = "        final int account = fragment == null ? UserConfig.selectedAccount : fragment.getCurrentAccount();"
        last_account = source.rfind(account_line)
        if last_account < 0:
            raise SystemExit("Original Premium purchase account declaration not found.")
        source = source[:last_account] + "        // Account was resolved before local Freemium activation.\n" + source[last_account + len(account_line):]

    PREMIUM_PREVIEW.write_text(source, encoding="utf-8")

def apply_freemium() -> None:
    if not (UPSTREAM_ROOT / "TMessagesProj/src/main/java/org/telegram/messenger/UserConfig.java").is_file():
        raise SystemExit("UserConfig.java is missing from upstream source.")
    if not PREMIUM_PREVIEW.is_file():
        raise SystemExit("PremiumPreviewFragment.java is missing from upstream source.")
    write_core()
    patch_premium_activation()

if __name__ == "__main__":
    apply_freemium()
