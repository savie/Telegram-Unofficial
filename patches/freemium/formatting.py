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
    # Reuse the existing TeleBetaFreemium engine generator. Do not edit patch.py.
    engine_source = ENGINE_PATCH.read_text(encoding="utf-8")
        source = """package org.telegram.messenger;
    
    import android.content.Context;
    import android.content.SharedPreferences;
    import java.util.Collections;
    import java.util.HashSet;
    import java.util.Set;
    
    /** Client-local Tele-beta entitlements, independent from Telegram Premium. */
    public final class TeleBetaFreemium {
        public enum Tier { FREE, FREEMIUM }
        public enum Feature { CUSTOM_THEMES, CHAT_CUSTOMIZATION, CUSTOM_UI, ADVANCED_DOWNLOADS, ADVANCED_PRIVACY, APP_ICONS }
    
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
    
        /** Whether the app-local Freemium tier has been durably granted. */
        public boolean isFreemiumActive() {
            return getTier() == Tier.FREEMIUM;
        }
    
        /** Grant the app-local Freemium tier without changing Telegram account premium. */
        public void grantFreemium() {
            Set<Feature> enabled = java.util.EnumSet.allOf(Feature.class);
            applyEntitlement(Tier.FREEMIUM, enabled);
        }
    
        public void applyEntitlement(Tier tier, Set<Feature> enabledFeatures) {
            if (tier == null) throw new IllegalArgumentException("tier must not be null");
            Set<String> values = new HashSet<>();
            if (tier == Tier.FREEMIUM && enabledFeatures != null) {
                for (Feature feature : enabledFeatures) if (feature != null) values.add(feature.name());
            }
            preferences.edit().putString(KEY_TIER, tier.name()).putStringSet(KEY_FEATURES, values).commit();
        }
    }
    """
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8")
    
    
    # The source generator above is the exact existing TeleBetaFreemium engine
    # from patch.py; extend its registry without duplicating the class.
    feature_old = "public enum Feature { CUSTOM_THEMES, CHAT_CUSTOMIZATION, CUSTOM_UI, ADVANCED_DOWNLOADS, ADVANCED_PRIVACY, APP_ICONS }"
    feature_new = "public enum Feature { CUSTOM_THEMES, CHAT_CUSTOMIZATION, CUSTOM_UI, ADVANCED_DOWNLOADS, ADVANCED_PRIVACY, APP_ICONS, RICH_EDITOR }"
    if engine_source.count(feature_old) == 1:
        engine_source = engine_source.replace(feature_old, feature_new, 1)
    elif engine_source.count(feature_new) != 1:
        raise SystemExit("Rich Editor feature registry anchor missing or ambiguous.")
    ENGINE_PATCH.write_text(engine_source, encoding="utf-8")

    # Gate 1: existing Rich Editor toolbar's premium-decorated buttons.
    rich_editor = ROOT / "TMessagesProj/src/main/java/org/telegram/ui/iv/RichEditor.java"
    source = rich_editor.read_text(encoding="utf-8")
    source = _ensure_import(
        source,
        "import org.telegram.messenger.UserConfig;\n",
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
    rich_editor.write_text(source, encoding="utf-8")

    # Gate 2: attach-alert send-button lock, separate from toolbar decoration.
    layout = ROOT / "TMessagesProj/src/main/java/org/telegram/ui/iv/ChatAttachAlertRichLayout.java"
    source = layout.read_text(encoding="utf-8")
    source = _ensure_import(
        source,
        "import org.telegram.messenger.UserConfig;\n",
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
    layout.write_text(source, encoding="utf-8")

    # Static contract: never rewrite Telegram Premium identity or protocol gate.
    changed_sources = rich_editor.read_text(encoding="utf-8") + layout.read_text(encoding="utf-8")
    forbidden = (
        "UserConfig.getInstance(currentAccount).setPremium",
        "TLRPC.User.premium =",
        "richEditorAllowed() {",
    )
    for token in forbidden:
        if token in changed_sources:
            raise SystemExit(f"Forbidden entitlement/protocol mutation detected: {token}")
