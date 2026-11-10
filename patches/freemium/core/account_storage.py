"""Generator untuk entitlement Freemium account-local berbasis clientUserId."""
from pathlib import Path

JAVA_CLASS = r'''package org.telegram.messenger;

import android.content.Context;
import android.content.SharedPreferences;

public final class TeleBetaFreemium {
    private static final String PREFIX = "telebeta_freemium_v2_";
    private static final int SCHEMA_VERSION = 2;

    private static SharedPreferences prefs(int account) {
        if (account < 0 || account >= UserConfig.MAX_ACCOUNT_COUNT) {
            return null;
        }
        long userId = UserConfig.getInstance(account).getClientUserId();
        if (userId <= 0 || ApplicationLoader.applicationContext == null) {
            return null;
        }
        return ApplicationLoader.applicationContext.getSharedPreferences(
            PREFIX + userId,
            Context.MODE_PRIVATE
        );
    }

    public static boolean isActive(int account) {
        SharedPreferences preferences = prefs(account);
        return preferences != null
            && preferences.getInt("schema_version", 0) == SCHEMA_VERSION
            && preferences.getBoolean("active", false);
    }

    public static boolean activate(int account) {
        SharedPreferences preferences = prefs(account);
        return preferences != null && preferences.edit()
            .putInt("schema_version", SCHEMA_VERSION)
            .putBoolean("active", true)
            .commit();
    }

    // Used only by client-side feature/UI gates. It does not alter Telegram's
    // authenticated user object or claim server-side Telegram Premium status.
    public static boolean hasAllAccess(int account) {
        return UserConfig.isValidAccount(account)
            && (UserConfig.getInstance(account).isPremium() || isActive(account));
    }

    private TeleBetaFreemium() {}
}
'''

def stage_java_helper(upstream_root: Path) -> tuple[Path, str]:
    target = upstream_root / "TMessagesProj/src/main/java/org/telegram/messenger/TeleBetaFreemium.java"
    return target, JAVA_CLASS
