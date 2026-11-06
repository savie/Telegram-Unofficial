"""Fondasi entitlement Freemium lokal Tele-ß."""
import re
from pathlib import Path

ROOT = Path("upstream/Telegram-Android")

def apply_freemium():
    target = ROOT / "TMessagesProj/src/main/java/org/telegram/messenger/TeleBetaFreemium.java"
    if target.exists():
        raise SystemExit(f"Refusing to overwrite existing upstream file: {target}")
    source = """package org.telegram.messenger;

import android.content.Context;
import android.content.SharedPreferences;
import java.util.Collections;
import java.util.HashSet;
import java.util.Set;

/** Client-local Tele-beta entitlements, independent from Telegram Premium. */
public final class TeleBetaFreemium {
    public enum Tier { FREE, FREEMIUM }
    public enum Feature { CUSTOM_THEMES, CHAT_CUSTOMIZATION, CUSTOM_UI, ADVANCED_DOWNLOADS, ADVANCED_PRIVACY }

    private static final String PREFS = "telebeta_freemium";
    private static final String KEY_TIER = "tier";
    private static final String KEY_FEATURES = "features";
    private static volatile TeleBetaFreemium instance;
    private final SharedPreferences preferences;

    private TeleBetaFreemium(Context context) {
        preferences = context.getApplicationContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public static TeleBetaFreemium getInstance() {
        TeleBetaFreemium local = instance;
        if (local == null) {
            synchronized (TeleBetaFreemium.class) {
                local = instance;
                if (local == null) {
                    Context context = ApplicationLoader.applicationContext;
                    if (context == null) throw new IllegalStateException("Application context is not initialized");
                    instance = local = new TeleBetaFreemium(context);
                }
            }
        }
        return local;
    }

    public Tier getTier() {
        String value = preferences.getString(KEY_TIER, Tier.FREE.name());
        try { return Tier.valueOf(value); }
        catch (IllegalArgumentException | NullPointerException ignored) { return Tier.FREE; }
    }

    public boolean isFeatureEnabled(Feature feature) {
        if (feature == null || getTier() != Tier.FREEMIUM) return false;
        return preferences.getStringSet(KEY_FEATURES, Collections.emptySet()).contains(feature.name());
    }

    /** Future trusted Tele-beta entitlement integration only; never call from a client-side toggle. */
    public void applyEntitlement(Tier tier, Set<Feature> enabledFeatures) {
        if (tier == null) throw new IllegalArgumentException("tier must not be null");
        Set<String> values = new HashSet<>();
        if (tier == Tier.FREEMIUM && enabledFeatures != null) {
            for (Feature feature : enabledFeatures) if (feature != null) values.add(feature.name());
        }
        preferences.edit().putString(KEY_TIER, tier.name()).putStringSet(KEY_FEATURES, values).apply();
    }
}
"""
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")
    code = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
    if any(token in code for token in ("UserConfig.getInstance", "TLRPC.User", ".premium")):
        raise SystemExit("Freemium engine must not inspect Telegram account entitlement.")
    if "Tier.FREE.name()" not in source or "return false;" not in source:
        raise SystemExit("Freemium default-deny validation failed.")
    if not source.endswith("\n"):
        raise SystemExit("Freemium source must end with newline.")

