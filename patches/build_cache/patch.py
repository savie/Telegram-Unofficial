"""Aktifkan compiler launcher ccache pada konfigurasi native Telegram."""

from pathlib import Path

ROOT = Path("upstream/Telegram-Android")
TARGET = ROOT / "TMessagesProj/build.gradle"
MARKER = "'-DCMAKE_CXX_COMPILER_LAUNCHER=ccache'"
ARGUMENTS = """                arguments '-DANDROID_STL=c++_static', '-DANDROID_PLATFORM=android-23',
                    '-DCMAKE_C_COMPILER_LAUNCHER=ccache',
                    '-DCMAKE_CXX_COMPILER_LAUNCHER=ccache'"""


def configure_native_build_cache():
    source = TARGET.read_text(encoding="utf-8")
    if MARKER in source:
        if "'-DCMAKE_C_COMPILER_LAUNCHER=ccache'" not in source:
            raise SystemExit("Partial ccache CMake launcher configuration detected.")
        return

    original = """                arguments '-DANDROID_STL=c++_static', '-DANDROID_PLATFORM=android-23' //, '-DANDROID_SUPPORT_FLEXIBLE_PAGE_SIZES=ON'"""
    if source.count(original) != 1:
        raise SystemExit("Unexpected CMake arguments in TMessagesProj/build.gradle; refusing unsafe patch.")

    TARGET.write_text(source.replace(original, ARGUMENTS, 1), encoding="utf-8")
