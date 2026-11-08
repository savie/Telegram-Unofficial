"""Standalone Rich Editor Freemium gate patch.

This patch reuses the upstream RichEditor and its existing toolbar. It only
replaces Premium-client gates with the Tele-beta local entitlement.
"""
from pathlib import Path

ROOT = Path(".")
ENGINE_PATCH = Path("patches/freemium/patch.py")


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


def _ensure_import(source: str, anchor: str, import_line: str, label: str) -> str:
    if import_line in source:
        return source
    return _replace_once(source, anchor, anchor + import_line, label + " import")


def apply_rich_editor_freemium() -> None:
    # apply_freemium() already generated this class earlier in the orchestrator.
    engine_file = ROOT / "TMessagesProj/src/main/java/org/telegram/messenger/TeleBetaFreemium.java"
    if not engine_file.exists():
        raise SystemExit("TeleBetaFreemium.java missing; apply_freemium() must run first.")
    engine_java = engine_file.read_text(encoding="utf-8")
    old_feature = "public enum Feature { CUSTOM_THEMES, CHAT_CUSTOMIZATION, CUSTOM_UI, ADVANCED_DOWNLOADS, ADVANCED_PRIVACY, APP_ICONS }"
    new_feature = "public enum Feature { CUSTOM_THEMES, CHAT_CUSTOMIZATION, CUSTOM_UI, ADVANCED_DOWNLOADS, ADVANCED_PRIVACY, APP_ICONS, RICH_EDITOR }"
    if engine_java.count(old_feature) == 1:
        engine_java = engine_java.replace(old_feature, new_feature, 1)
        engine_file.write_text(engine_java, encoding="utf-8")
    elif engine_java.count(new_feature) != 1:
        raise SystemExit("Generated TeleBetaFreemium feature registry anchor missing or ambiguous.")

    # Gate 1: existing Rich Editor toolbar's premium-decorated buttons.
    rich_editor = ROOT / "TMessagesProj/src/main/java/org/telegram/ui/iv/RichEditor.java"
    source = rich_editor.read_text(encoding="utf-8")
    source = _ensure_import(
        source,
        "import org.telegram.messenger.MessagesController;\n",
        "import org.telegram.messenger.TeleBetaFreemium;\n",
        "RichEditor",
    )
    old_lock = """        final boolean premiumLock = !MessagesController.getInstance(currentAccount).richEditorAllowed() && !UserConfig.getInstance(currentAccount).isPremium();
        for (Button b : premiumButtons) {"""
    new_lock = """        final boolean premiumLock = !MessagesController.getInstance(currentAccount).richEditorAllowed()
            && !UserConfig.getInstance(currentAccount).isPremium()
            && !TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.RICH_EDITOR);
        for (Button b : premiumButtons) {"""
    if old_lock in source:
        source = _replace_once(source, old_lock, new_lock, "RichEditor premium button lock")
    elif source.count(new_lock) != 1:
        raise SystemExit("RichEditor premium button lock is in an unknown state.")

    old_send_lock = """        return !MessagesController.getInstance(currentAccount).richEditorAllowed()
            && !UserConfig.getInstance(currentAccount).isPremium()
            && listView.isLossy();"""
    new_send_lock = """        return !MessagesController.getInstance(currentAccount).richEditorAllowed()
            && !UserConfig.getInstance(currentAccount).isPremium()
            && !TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.RICH_EDITOR)
            && listView.isLossy();"""
    if old_send_lock in source:
        source = _replace_once(source, old_send_lock, new_send_lock, "RichEditor lossy send lock")
    elif source.count(new_send_lock) != 1:
        raise SystemExit("RichEditor lossy send lock is in an unknown state.")

    # The attach-alert's own lossy send predicate is a second enforcement path.
    attach_send_lock = """        return !MessagesController.getInstance(currentAccount).richEditorAllowed()
            && !UserConfig.getInstance(currentAccount).isPremium()
            && listView.isLossy();"""
    attach_send_unlock = """        return !MessagesController.getInstance(currentAccount).richEditorAllowed()
            && !UserConfig.getInstance(currentAccount).isPremium()
            && !TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.RICH_EDITOR)
            && listView.isLossy();"""
    if attach_send_lock in source:
        source = _replace_once(source, attach_send_lock, attach_send_unlock, "ChatAttachAlertRichLayout lossy send predicate")
    elif source.count(attach_send_unlock) != 1:
        raise SystemExit("ChatAttachAlertRichLayout lossy send predicate is in an unknown state.")

    old_conversion = """            if (!UserConfig.getInstance(currentAccount).isPremium()) {
                showDialog(new PremiumFeatureBottomSheet(this, PremiumPreviewFragment.PREMIUM_FEATURE_RICH_EDITOR, true));
            }"""
    new_conversion = """            if (!UserConfig.getInstance(currentAccount).isPremium()
                && !TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.RICH_EDITOR)) {
                showDialog(new PremiumFeatureBottomSheet(this, PremiumPreviewFragment.PREMIUM_FEATURE_RICH_EDITOR, true));
            }"""
    if old_conversion in source:
        source = _replace_once(source, old_conversion, new_conversion, "RichEditor conversion paywall")
    elif source.count(new_conversion) != 1:
        raise SystemExit("RichEditor conversion paywall is in an unknown state.")
    # Existing block-type menu has its own Premium decoration gate, separate
    # from the toolbar-wide premiumButtons list.
    menu_lock = """            final boolean premiumLock = !MessagesController.getInstance(currentAccount).richEditorAllowed() && !UserConfig.getInstance(currentAccount).isPremium();"""
    menu_unlock = """            final boolean premiumLock = !MessagesController.getInstance(currentAccount).richEditorAllowed()
                && !UserConfig.getInstance(currentAccount).isPremium()
                && !TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.RICH_EDITOR);"""
    if menu_lock in source:
        source = _replace_once(source, menu_lock, menu_unlock, "RichEditor block menu lock")
    elif source.count(menu_unlock) != 1:
        raise SystemExit("RichEditor block menu lock is in an unknown state.")
    rich_editor.write_text(source, encoding="utf-8")

    # Gate 2: attach-alert send-button lock, separate from toolbar decoration.
    layout = ROOT / "TMessagesProj/src/main/java/org/telegram/ui/iv/ChatAttachAlertRichLayout.java"
    source = layout.read_text(encoding="utf-8")
    source = _ensure_import(
        source,
        "import org.telegram.messenger.MessagesController;\n",
        "import org.telegram.messenger.TeleBetaFreemium;\n",
        "ChatAttachAlertRichLayout",
    )
    old_layout_lock = """            final boolean premiumLocked = !MessagesController.getInstance(currentAccount).richEditorAllowed()
                && !UserConfig.getInstance(currentAccount).isPremium();"""
    new_layout_lock = """            final boolean premiumLocked = !MessagesController.getInstance(currentAccount).richEditorAllowed()
                && !UserConfig.getInstance(currentAccount).isPremium()
                && !TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.RICH_EDITOR);"""
    if old_layout_lock in source:
        source = _replace_once(source, old_layout_lock, new_layout_lock, "ChatAttachAlertRichLayout send lock")
    elif source.count(new_layout_lock) != 1:
        raise SystemExit("ChatAttachAlertRichLayout send lock is in an unknown state.")

    old_preview = """        if (!UserConfig.getInstance(currentAccount).isPremium()) {
            new PremiumFeatureBottomSheet(parentAlert.baseFragment, getContext(), currentAccount, PremiumPreviewFragment.PREMIUM_FEATURE_RICH_EDITOR, true).show();
            return true;
        }"""
    new_preview = """        if (!UserConfig.getInstance(currentAccount).isPremium()
            && !TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.RICH_EDITOR)) {
            new PremiumFeatureBottomSheet(parentAlert.baseFragment, getContext(), currentAccount, PremiumPreviewFragment.PREMIUM_FEATURE_RICH_EDITOR, true).show();
            return true;
        }"""
    if old_preview in source:
        source = _replace_once(source, old_preview, new_preview, "Rich Article send preview paywall")
    elif source.count(new_preview) != 1:
        raise SystemExit("Rich Article send preview paywall is in an unknown state.")
    # Rich Article text-type menu has a separate Premium-decorated heading gate.
    menu_lock = """        final boolean premiumLock = !MessagesController.getInstance(currentAccount).richEditorAllowed() && !UserConfig.getInstance(currentAccount).isPremium();"""
    menu_unlock = """        final boolean premiumLock = !MessagesController.getInstance(currentAccount).richEditorAllowed()
            && !UserConfig.getInstance(currentAccount).isPremium()
            && !TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.RICH_EDITOR);"""
    if menu_lock in source:
        source = _replace_once(source, menu_lock, menu_unlock, "ChatAttachAlertRichLayout text-type menu lock")
    elif source.count(menu_unlock) != 1:
        raise SystemExit("ChatAttachAlertRichLayout text-type menu lock is in an unknown state.")

    # Send preview and conversion sheet are independent direct Premium gates.
    old_conversion = """            if (!UserConfig.getInstance(currentAccount).isPremium()) {
                new PremiumFeatureBottomSheet(parentAlert.baseFragment, getContext(), currentAccount, PremiumPreviewFragment.PREMIUM_FEATURE_RICH_EDITOR, true).show();
            }"""
    new_conversion = """            if (!UserConfig.getInstance(currentAccount).isPremium()
                && !TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.RICH_EDITOR)) {
                new PremiumFeatureBottomSheet(parentAlert.baseFragment, getContext(), currentAccount, PremiumPreviewFragment.PREMIUM_FEATURE_RICH_EDITOR, true).show();
            }"""
    if old_conversion in source:
        source = _replace_once(source, old_conversion, new_conversion, "ChatAttachAlertRichLayout conversion paywall")
    elif source.count(new_conversion) != 1:
        raise SystemExit("ChatAttachAlertRichLayout conversion paywall is in an unknown state.")

    layout.write_text(source, encoding="utf-8")

    # Static contract: the patch changes only client-side entitlement gates.
    changed_sources = rich_editor.read_text(encoding="utf-8") + layout.read_text(encoding="utf-8")
    if "TeleBetaFreemium.Feature.RICH_EDITOR" not in changed_sources:
        raise SystemExit("Rich Editor entitlement checks were not applied.")
    if "richEditorAllowed() {" in changed_sources or "TLRPC.User.premium =" in changed_sources:
        raise SystemExit("Protocol/account entitlement mutation detected.")
