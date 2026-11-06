"""Pengaturan Google Services dan Firebase untuk aplikasi standalone Tele-ß."""
import json
import os
from pathlib import Path

ROOT = Path("upstream/Telegram-Android")
GOOGLE_SERVICES_PLUGIN = "apply plugin: 'com.google.gms.google-services'"

def configure_firebase():
    module = ROOT / "TMessagesProj/build.gradle"
    standalone = ROOT / "TMessagesProj_AppStandalone/build.gradle"
    module_text = module.read_text(encoding="utf-8")
    app_text = standalone.read_text(encoding="utf-8")
    if module_text.count(GOOGLE_SERVICES_PLUGIN) != 1:
        raise SystemExit("Deklarasi Google Services plugin pada library tidak sesuai baseline.")
    module.write_text(module_text.replace(GOOGLE_SERVICES_PLUGIN, "", 1), encoding="utf-8")
    if app_text.count(GOOGLE_SERVICES_PLUGIN) != 1:
        raise SystemExit("Google Services plugin standalone harus sudah tersedia dari upstream.")

    (ROOT / "TMessagesProj/google-services.json").unlink(missing_ok=True)
    firebase_text = os.environ.get("FIREBASE_GOOGLE_SERVICES_JSON", "").strip()
    if not firebase_text:
        raise SystemExit("FIREBASE_GOOGLE_SERVICES_JSON wajib diatur.")
    try:
        config = json.loads(firebase_text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"FIREBASE_GOOGLE_SERVICES_JSON bukan JSON valid: {exc}") from exc
    clients = config.get("client", [])
    if not any(c.get("client_info", {}).get("android_client_info", {}).get("package_name") == "org.telebeta.messenger" for c in clients):
        raise SystemExit("Konfigurasi Firebase tidak memiliki client Android org.telebeta.messenger.")
    app_json = ROOT / "TMessagesProj_AppStandalone/google-services.json"
    app_json.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    if GOOGLE_SERVICES_PLUGIN in module.read_text(encoding="utf-8"):
        raise SystemExit("Google Services plugin masih aktif pada library.")
    if GOOGLE_SERVICES_PLUGIN not in standalone.read_text(encoding="utf-8"):
        raise SystemExit("Google Services plugin standalone hilang.")
