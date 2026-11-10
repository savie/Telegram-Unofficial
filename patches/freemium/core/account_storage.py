"""Generator untuk entitlement Freemium account-local berbasis clientUserId."""
from pathlib import Path

from .account_identity import resolve_client_user_id_expression

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
        long userId = accountUserId(account);
        if (userId <= 0 || ApplicationLoader.applicationContext == null) {
            return null;
        }
        return ApplicationLoader.applicationContext.getSharedPreferences(
            PREFIX + userId,
            Context.MODE_PRIVATE
        );
    }

    private static long accountUserId(int account) {
        if (!UserConfig.isValidAccount(account)) {
            return 0L;
        }
        return UserConfig.getInstance(account).getClientUserId();
    }

    public static boolean isActive(int account) {
        SharedPreferences preferences = prefs(account);
        return preferences != null
            && preferences.getInt("schema_version", 0) == SCHEMA_VERSION
            && preferences.getBoolean("active", false);
    }

    public static boolean activate(int account) {
        SharedPreferences preferences = prefs(account);
        if (preferences == null) {
            return false;
        }
        long now = System.currentTimeMillis();
        long activatedAt = preferences.getLong("activated_at", 0L);
        SharedPreferences.Editor editor = preferences.edit()
            .putInt("schema_version", SCHEMA_VERSION)
            .putBoolean("active", true)
            .putLong("activated_at", activatedAt > 0L ? activatedAt : now)
            .putLong("updated_at", now);
        return editor.commit();
    }

    // Client-side entitlement only; never mutate Telegram's authenticated user state.
    public static boolean hasAllAccess(int account) {
        return UserConfig.isValidAccount(account)
            && (UserConfig.getInstance(account).isPremium() || isActive(account));
    }

    private TeleBetaFreemium() {}
}
'''

def stage_java_helper(upstream_root: Path) -> tuple[Path, str]:
    target = upstream_root / "TMessagesProj/src/main/java/org/telegram/messenger/TeleBetaFreemium.java"
    return target, JAVA_CLASS.replace(
        "UserConfig.getInstance(account).getClientUserId()",
        resolve_client_user_id_expression("account"),
    )
