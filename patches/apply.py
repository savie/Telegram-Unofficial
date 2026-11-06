#!/usr/bin/env python3
"""Apply Tele-beta build-time patches to the pinned Telegram Android source."""
import base64
import json
import os
import re
from pathlib import Path

ROOT = Path("upstream/Telegram-Android")

def replace_once(path: Path, pattern: str, replacement: str, label: str, flags=0):
    original = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, original, count=1, flags=flags)
    if count != 1:
        raise SystemExit(f"Patch target changed or missing: {label}")
    path.write_text(updated, encoding="utf-8")

def configure_api():
    path = ROOT / "TMessagesProj/src/main/java/org/telegram/messenger/BuildVars.java"
    app_id = os.environ["TELEGRAM_API_ID"]
    app_hash = os.environ["TELEGRAM_API_HASH"]
    if not app_id.isdigit():
        raise SystemExit("TELEGRAM_API_ID must be numeric.")
    source = path.read_text(encoding="utf-8")
    source, n1 = re.subn(r"public static int APP_ID = [0-9]+;", f"public static int APP_ID = {app_id};", source, count=1)
    source, n2 = re.subn(r'public static String APP_HASH = "[^"]*";', f'public static String APP_HASH = "{app_hash}";', source, count=1)
    if n1 != 1 or n2 != 1:
        raise SystemExit("BuildVars.java layout changed; refusing to patch credentials.")
    path.write_text(source, encoding="utf-8")

def configure_signing():
    names = ("TELEBETA_KEYSTORE_BASE64", "TELEBETA_KEYSTORE_PASSWORD", "TELEBETA_KEY_ALIAS", "TELEBETA_KEY_PASSWORD")
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        raise SystemExit("Missing repository secrets: " + ", ".join(missing))
    alias = os.environ["TELEBETA_KEY_ALIAS"]
    if alias != "telebeta-release":
        raise SystemExit("TELEBETA_KEY_ALIAS must be telebeta-release.")
    try:
        raw = base64.b64decode("".join(os.environ["TELEBETA_KEYSTORE_BASE64"].split()), validate=True)
    except Exception as exc:
        raise SystemExit("TELEBETA_KEYSTORE_BASE64 is not valid Base64.") from exc
    if len(raw) < 1024:
        raise SystemExit("Decoded keystore is unexpectedly small.")
    keystore = ROOT / "TMessagesProj/config/release.keystore"
    keystore.parent.mkdir(parents=True, exist_ok=True)
    keystore.write_bytes(raw)
    props = ROOT / "gradle.properties"
    data = props.read_text(encoding="utf-8")
    values = {
        "RELEASE_STORE_PASSWORD": os.environ["TELEBETA_KEYSTORE_PASSWORD"],
        "RELEASE_KEY_ALIAS": alias,
        "RELEASE_KEY_PASSWORD": os.environ["TELEBETA_KEY_PASSWORD"],
    }
    for key, value in values.items():
        data, count = re.subn(rf"(?m)^{key}=.*$", lambda _: f"{key}={value}", data, count=1)
        if count != 1:
            raise SystemExit(f"Could not configure {key}.")
    props.write_text(data, encoding="utf-8")

def configure_branding_firebase():
    props = ROOT / "gradle.properties"
    replace_once(props, r"(?m)^APP_PACKAGE=.*$", "APP_PACKAGE=org.telebeta.messenger", "APP_PACKAGE")
    manifest = ROOT / "TMessagesProj/config/release/AndroidManifest_standalone.xml"
    replace_once(manifest, r'android:label="[^"]*"', 'android:label="Tele-ß"', "launcher label")

    module = ROOT / "TMessagesProj/build.gradle"
    module_text = module.read_text(encoding="utf-8")
    if not re.search(r"namespace ['\"]org\.telegram\.messenger['\"]", module_text):
        raise SystemExit("TMessagesProj namespace must remain org.telegram.messenger.")
    plugin = "apply plugin: 'com.google.gms.google-services'"
    if module_text.count(plugin) != 1:
        raise SystemExit("Unexpected Google Services plugin declaration in TMessagesProj.")
    module.write_text(module_text.replace(plugin, "", 1), encoding="utf-8")

    standalone = ROOT / "TMessagesProj_AppStandalone/build.gradle"
    app_text = standalone.read_text(encoding="utf-8")
    if "namespace 'org.telegram.messenger.web'" not in app_text and 'namespace "org.telegram.messenger.web"' not in app_text:
        raise SystemExit("Standalone namespace must remain org.telegram.messenger.web.")
    app_text, count = re.subn(r'(standalone\s*\{[\s\S]*?applicationIdSuffix\s+)["\']\.web["\']', r'\1""', app_text, count=1)
    if count != 1:
        raise SystemExit("Could not remove standalone .web applicationIdSuffix.")
    standalone.write_text(app_text, encoding="utf-8")

    (ROOT / "TMessagesProj/google-services.json").unlink(missing_ok=True)
    firebase_text = os.environ.get("FIREBASE_GOOGLE_SERVICES_JSON", "").strip()
    if not firebase_text:
        raise SystemExit("FIREBASE_GOOGLE_SERVICES_JSON is required.")
    try:
        config = json.loads(firebase_text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"FIREBASE_GOOGLE_SERVICES_JSON is invalid JSON: {exc}") from exc
    clients = config.get("client", [])
    if not any(c.get("client_info", {}).get("android_client_info", {}).get("package_name") == "org.telebeta.messenger" for c in clients):
        raise SystemExit("Firebase config has no Android client for org.telebeta.messenger.")
    app_firebase = ROOT / "TMessagesProj_AppStandalone/google-services.json"
    app_firebase.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    if plugin not in standalone.read_text(encoding="utf-8"):
        raise SystemExit("Google Services plugin must remain enabled in standalone app.")
    if plugin in module.read_text(encoding="utf-8"):
        raise SystemExit("Google Services plugin must not be enabled in library module.")
    final_props = props.read_text(encoding="utf-8")
    if "APP_PACKAGE=org.telebeta.messenger" not in final_props:
        raise SystemExit("APP_PACKAGE identity validation failed.")

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

if __name__ == "__main__":
    configure_api()
    configure_signing()
    configure_branding_firebase()
    apply_freemium()
    print("All Tele-beta build patches applied.")
