"""Pengaturan Firebase untuk aplikasi standalone Tele-ß."""
import json
import os
from pathlib import Path

ROOT = Path("upstream/Telegram-Android")
PLUGIN = "apply plugin: 'com.google.gms.google-services'"

def remove_library_google_services_plugin():
    module = ROOT / "TMessagesProj/build.gradle"
    module_text = module.read_text(encoding="utf-8")
    if module_text.count(PLUGIN) != 1:
        raise SystemExit("Unexpected Google Services plugin declaration in TMessagesProj.")
    module.write_text(module_text.replace(PLUGIN, "", 1), encoding="utf-8")

def configure_firebase():
    module = ROOT / "TMessagesProj/build.gradle"
    standalone = ROOT / "TMessagesProj_AppStandalone/build.gradle"
    props = ROOT / "gradle.properties"

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

    if PLUGIN not in standalone.read_text(encoding="utf-8"):
        raise SystemExit("Google Services plugin must remain enabled in standalone app.")
    if PLUGIN in module.read_text(encoding="utf-8"):
        raise SystemExit("Google Services plugin must not be enabled in library module.")
    final_props = props.read_text(encoding="utf-8")
    if "APP_PACKAGE=org.telebeta.messenger" not in final_props:
        raise SystemExit("APP_PACKAGE identity validation failed.")
