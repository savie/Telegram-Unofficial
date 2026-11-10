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
