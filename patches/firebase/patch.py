"""Pengaturan Google Services dan Firebase untuk aplikasi standalone Tele-ß."""
import json
import os
import re
from pathlib import Path

ROOT = Path("upstream/Telegram-Android")
GOOGLE_SERVICES_PLUGIN = "apply plugin: 'com.google.gms.google-services'"


def configure_firebase() -> None:
    library_gradle = ROOT / "TMessagesProj/build.gradle"
    standalone_gradle = ROOT / "TMessagesProj_AppStandalone/build.gradle"

    library_text = library_gradle.read_text(encoding="utf-8")
    standalone_text = standalone_gradle.read_text(encoding="utf-8")

    # Plugin Google Services must only be applied by the standalone application.
    # Remove any existing library declaration (0 or 1); reject ambiguous duplicates.
    library_count = library_text.count(GOOGLE_SERVICES_PLUGIN)
    if library_count > 1:
        raise SystemExit("Deklarasi Google Services plugin duplikat pada library.")
    if library_count == 1:
        library_text = library_text.replace(GOOGLE_SERVICES_PLUGIN, "", 1)
        library_gradle.write_text(library_text, encoding="utf-8")

    standalone_count = standalone_text.count(GOOGLE_SERVICES_PLUGIN)
    if standalone_count > 1:
        raise SystemExit("Deklarasi Google Services plugin duplikat pada standalone.")
    if standalone_count == 0:
        # Place the plugin next to the existing module-level apply statements.
        standalone_text = standalone_text.rstrip() + "\n" + GOOGLE_SERVICES_PLUGIN + "\n"
        standalone_gradle.write_text(standalone_text, encoding="utf-8")

    firebase_text = os.environ.get("FIREBASE_GOOGLE_SERVICES_JSON", "").strip()
    if not firebase_text:
        raise SystemExit("FIREBASE_GOOGLE_SERVICES_JSON wajib diatur.")
    try:
        config = json.loads(firebase_text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"FIREBASE_GOOGLE_SERVICES_JSON bukan JSON valid: {exc}") from exc

    clients = config.get("client", [])
    package_name = "org.telebeta.messenger"
    if not any(
        client.get("client_info", {})
        .get("android_client_info", {})
        .get("package_name") == package_name
        for client in clients
    ):
        raise SystemExit(
            f"Konfigurasi Firebase tidak memiliki client Android {package_name}."
        )

    library_json = ROOT / "TMessagesProj/google-services.json"
    app_json = ROOT / "TMessagesProj_AppStandalone/google-services.json"
    library_json.unlink(missing_ok=True)
    app_json.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    final_library = library_gradle.read_text(encoding="utf-8")
    final_standalone = standalone_gradle.read_text(encoding="utf-8")
    if GOOGLE_SERVICES_PLUGIN in final_library:
        raise SystemExit("Google Services plugin masih aktif pada modul library.")
    if final_standalone.count(GOOGLE_SERVICES_PLUGIN) != 1:
        raise SystemExit("Google Services plugin harus aktif tepat satu kali pada standalone.")
    if not app_json.is_file() or library_json.exists():
        raise SystemExit("Penempatan google-services.json tidak sesuai.")
