"""Local theme, personal wallpaper, and chat theme persistence."""


def _replace_exact(source: str, old: str, new: str, expected: int, label: str) -> str:
    old_count = source.count(old)
    new_count = source.count(new)
    if old_count == expected:
        return source.replace(old, new, expected)
    if old_count == 0 and new_count == expected:
        return source
    raise RuntimeError(
        f"{label}: expected {expected} anchor(s), found old={old_count}, patched={new_count}"
    )


def _ensure_import(source: str, anchor: str, import_line: str, label: str) -> str:
    if import_line in source:
        return source
    if source.count(anchor) != 1:
        raise RuntimeError(f"{label}: import anchor must occur exactly once")
    return source.replace(anchor, anchor + import_line, 1)


def patch_theme(source: str) -> str:
    source = _ensure_import(
        source,
        "import org.telegram.messenger.MessagesController;\\n",
        "import org.telegram.messenger.TeleBetaFreemium;\\n",
        "Theme",
    )
    return _replace_exact(
        source,
        """        if (finalSave) {
            MessagesController.getInstance(themeInfo.account).saveThemeToServer(themeInfo, themeInfo.getAccent(false));
        }""",
        """        if (finalSave && !TeleBetaFreemium.isActive(themeInfo.account)) {
            MessagesController.getInstance(themeInfo.account).saveThemeToServer(themeInfo, themeInfo.getAccent(false));
        }""",
        1,
        "Theme local save bypass",
    )


def patch_theme_preview_activity(source: str) -> str:
    source = _ensure_import(
        source,
        "import org.telegram.messenger.MessagesController;\\n",
        "import org.telegram.messenger.TeleBetaFreemium;\\n",
        "ThemePreviewActivity",
    )
    source = _replace_exact(
        source,
        "        MessagesController.getInstance(currentAccount).saveWallpaperToServer(path, wallpaperInfo, slug != null && dialogId == 0, 0);",
        """        boolean teleBetaLocalPersonalWallpaper = dialogId == 0 && TeleBetaFreemium.isActive(currentAccount);
        if (!teleBetaLocalPersonalWallpaper) {
            MessagesController.getInstance(currentAccount).saveWallpaperToServer(path, wallpaperInfo, slug != null && dialogId == 0, 0);
        }""",
        1,
        "personal wallpaper server-save bypass",
    )
    return _replace_exact(
        source,
        """                Theme.getActiveTheme().setOverrideWallpaper(wallpaperInfo);
                Theme.reloadWallpaper(true);""",
        """                Theme.getActiveTheme().setOverrideWallpaper(wallpaperInfo);
                Theme.reloadWallpaper(true);
                if (teleBetaLocalPersonalWallpaper) {
                    Theme.saveCurrentTheme(Theme.getActiveTheme(), false, false, false);
                }""",
        1,
        "personal wallpaper local persistence",
    )


def patch_chat_theme_bottom_sheet(source: str) -> str:
    source = _ensure_import(
        source,
        "import org.telegram.messenger.ChatThemeController;\\n",
        "import org.telegram.messenger.TeleBetaFreemium;\\n",
        "ChatThemeBottomSheet",
    )
    return _replace_exact(
        source,
        "            ChatThemeController.getInstance(currentAccount).setDialogTheme(chatActivity.getDialogId(), tlChatTheme, true);",
        """            boolean teleBetaLocalTheme = TeleBetaFreemium.isActive(currentAccount);
            ChatThemeController.getInstance(currentAccount).setDialogTheme(chatActivity.getDialogId(), tlChatTheme, !teleBetaLocalTheme);""",
        1,
        "chat theme server-sync bypass",
    )


TARGETS = (
    "ui/ActionBar/Theme.java",
    "ui/ThemePreviewActivity.java",
    "ui/Components/ChatThemeBottomSheet.java",
)
