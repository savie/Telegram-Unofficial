"""Generator untuk SharedPreferences account-local berbasis clientUserId."""
from pathlib import Path

JAVA_CLASS = r'''package org.telegram.messenger;

import android.content.Context;
import android.content.SharedPreferences;

public final class TeleBetaFreemium {
    private static final String PREFIX = "telebeta_freemium_v2_";
    private static final int SCHEMA_VERSION = 2;
    private static SharedPreferences prefs(int account) {
        long userId = UserConfig.getInstance(account).getClientUserId();
        if (userId <= 0 || ApplicationLoader.applicationContext == null) return null;
        return ApplicationLoader.applicationContext.getSharedPreferences(PREFIX + userId, Context.MODE_PRIVATE);
    }
    public static boolean isActive(int account) {
        SharedPreferences p = prefs(account);
        return p != null && p.getInt("schema_version", SCHEMA_VERSION) == SCHEMA_VERSION && p.getBoolean("active", false);
    }
    public static boolean activate(int account) {
        SharedPreferences p = prefs(account);
        return p != null && p.edit().putInt("schema_version", SCHEMA_VERSION).putBoolean("active", true).commit();
    }
    public static boolean hasAllAccess(int account) { return isActive(account); }
    private TeleBetaFreemium() {}
}
'''

def stage_java_helper(upstream_root: Path) -> tuple[Path, str]:
    target = upstream_root / "TMessagesProj/src/main/java/org/telegram/messenger/TeleBetaFreemium.java"
    return target, JAVA_CLASS
