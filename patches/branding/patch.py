"""Pengaturan identitas aplikasi Tele-ß dan kredensial Telegram."""
import os
import re
from pathlib import Path

ROOT = Path("upstream/Telegram-Android")

def replace_once(path: Path, pattern: str, replacement: str, label: str, flags=0):
    original = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, original, count=1, flags=flags)
    if count != 1:
        raise SystemExit(f"Patch target berubah atau tidak ditemukan: {label}")
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

def configure_branding():
    props = ROOT / "gradle.properties"
    replace_once(props, r"(?m)^APP_PACKAGE=.*$", "APP_PACKAGE=org.telebeta.messenger", "APP_PACKAGE")
    manifest = ROOT / "TMessagesProj/config/release/AndroidManifest_standalone.xml"
    replace_once(manifest, r'android:label="[^"]*"', 'android:label="Tele-ß"', "label aplikasi")

    library = ROOT / "TMessagesProj/build.gradle"
    library_text = library.read_text(encoding="utf-8")
    if not re.search(r"""namespace ['"]org\.telegram\.messenger['"]""", library_text):
        raise SystemExit("Namespace library harus tetap org.telegram.messenger.")

    standalone = ROOT / "TMessagesProj_AppStandalone/build.gradle"
    app_text = standalone.read_text(encoding="utf-8")
    if "namespace 'org.telegram.messenger.web'" not in app_text and 'namespace "org.telegram.messenger.web"' not in app_text:
        raise SystemExit("Namespace standalone harus tetap org.telegram.messenger.web.")
    build_types_match = re.search(r"\\bbuildTypes\\s*\\{", app_text)
    if not build_types_match:
        raise SystemExit("Could not locate buildTypes block in standalone Gradle file.")

    def find_block_end(text: str, opening_brace: int) -> int:
        depth = 0
        for index in range(opening_brace, len(text)):
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
                if depth == 0:
                    return index + 1
        raise SystemExit("Unbalanced braces in standalone Gradle file.")

    build_open = app_text.find("{", build_types_match.start())
    build_end = find_block_end(app_text, build_open)
    build_types_text = app_text[build_types_match.start():build_end]
    standalone_match = re.search(r"\\bstandalone\\s*\\{", build_types_text)
    if not standalone_match:
        raise SystemExit("Could not locate buildTypes.standalone block.")

    standalone_open = build_types_text.find("{", standalone_match.start())
    standalone_end = find_block_end(build_types_text, standalone_open)
    standalone_text = build_types_text[standalone_match.start():standalone_end]
    standalone_text, count = re.subn(
        r'(applicationIdSuffix\\s+)["\\']\\.web["\\']',
        r'\\1""',
        standalone_text,
        count=1,
    )
    if count != 1:
        raise SystemExit("Could not remove applicationIdSuffix .web from buildTypes.standalone.")

    updated_build_types = (
        build_types_text[:standalone_match.start()]
        + standalone_text
        + build_types_text[standalone_end:]
    )
    app_text = (
        app_text[:build_types_match.start()]
        + updated_build_types
        + app_text[build_end:]
    )
    standalone.write_text(app_text, encoding="utf-8")
    if "APP_PACKAGE=org.telebeta.messenger" not in props.read_text(encoding="utf-8"):
        raise SystemExit("Validasi identitas APP_PACKAGE gagal.")
