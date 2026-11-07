"""Entitlement lokal dan jalur Grant Freemium Tele-ß."""
import re
from pathlib import Path

ROOT = Path(".")

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

    preview = ROOT / "TMessagesProj/src/main/java/org/telegram/ui/PremiumPreviewFragment.java"
    preview_source = preview.read_text(encoding="utf-8")
    import_line = "import org.telegram.messenger.TeleBetaFreemium;\n"
    anchor = "import org.telegram.messenger.UserObject;\n"
    if import_line not in preview_source:
        if preview_source.count(anchor) != 1:
            raise SystemExit("Could not locate PremiumPreviewFragment import anchor.")
        preview_source = preview_source.replace(anchor, anchor + import_line, 1)

    purchase_signature = "public static void buyPremium(BaseFragment fragment, SubscriptionTier tier, String source, boolean forcePremium, BillingFlowParams.SubscriptionUpdateParams updateParams) {"
    purchase_end = "\n    public static String getPremiumButtonText"
    grant_method = """public static void buyPremium(BaseFragment fragment, SubscriptionTier tier, String source, boolean forcePremium, BillingFlowParams.SubscriptionUpdateParams updateParams) {
        // Grant the app-local tier, then show Telegram's existing subscription-success layout.
        TeleBetaFreemium.getInstance().grantFreemium();
        if (fragment != null) {
            fragment.presentFragment(new PremiumPreviewFragment("freemium").setForcePremium());
        }
    }

"""
    if preview_source.count(purchase_signature) != 1:
        raise SystemExit("Premium purchase entry point is missing or ambiguous; refusing to patch.")
    purchase_start_index = preview_source.index(purchase_signature)
    purchase_end_index = preview_source.find(purchase_end, purchase_start_index)
    if purchase_end_index < 0:
        raise SystemExit("Premium purchase method boundary changed; refusing to patch.")
    preview_source = preview_source[:purchase_start_index] + grant_method + preview_source[purchase_end_index:]

    button_signature = "public static String getPremiumButtonText(int currentAccount, SubscriptionTier tier) {"
    button_end = "\n    private void measureGradient"
    button_method = """public static String getPremiumButtonText(int currentAccount, SubscriptionTier tier) {
        return "Aktifkan Freemium";
    }

"""
    if preview_source.count(button_signature) != 1:
        raise SystemExit("Premium button method is missing or ambiguous; refusing to patch.")
    button_start_index = preview_source.index(button_signature)
    button_end_index = preview_source.find(button_end, button_start_index)
    if button_end_index < 0:
        raise SystemExit("Premium button method boundary changed; refusing to patch.")
    preview_source = preview_source[:button_start_index] + button_method + preview_source[button_end_index:]
    constructor_signature = "public PremiumPreviewFragment(int type, String source) {"
    constructor_guard = """        this.type = type;
        whiteBackground = !Theme.isCurrentThemeDark() && type == FEATURES_BUSINESS;
        this.source = source;"""
    constructor_guard_replacement = """        this.type = type;
        whiteBackground = !Theme.isCurrentThemeDark() && type == FEATURES_BUSINESS;
        this.source = source;
        // Rehydrate the success presentation from the durable Tele-beta grant.
        if ("freemium".equals(source) && TeleBetaFreemium.getInstance().isFreemiumActive()) {
            forcePremium = true;
        }"""
    if preview_source.count(constructor_signature) != 1 or preview_source.count(constructor_guard) != 1:
        raise SystemExit("PremiumPreviewFragment constructor anchor missing or ambiguous; refusing to patch.")
    preview_source = preview_source.replace(constructor_guard, constructor_guard_replacement, 1)

    success_state = "AndroidUtilities.updateViewVisibilityAnimated(buttonContainer, !getUserConfig().isPremium() || currentSubscriptionTier != null && currentSubscriptionTier.getMonths() < subscriptionTiers.get(selectedTierIndex).getMonths() && !forcePremium, 1f, false);"
    success_state_replacement = "AndroidUtilities.updateViewVisibilityAnimated(buttonContainer, (!getUserConfig().isPremium() && !forcePremium) || currentSubscriptionTier != null && currentSubscriptionTier.getMonths() < subscriptionTiers.get(selectedTierIndex).getMonths() && !forcePremium, 1f, false);"
    if preview_source.count(success_state) != 1:
        raise SystemExit("Could not uniquely locate Premium success-state button visibility.")
    preview_source = preview_source.replace(success_state, success_state_replacement, 1)
    preview.write_text(preview_source, encoding="utf-8")

    # App icons are entirely local Android launcher components. Keep Telegram's
    # account entitlement untouched and allow this capability through Tele-beta.
    icon_selector = ROOT / "TMessagesProj/src/main/java/org/telegram/ui/Cells/AppIconsSelectorCell.java"
    icon_source = icon_selector.read_text(encoding="utf-8")
    icon_import = "import org.telegram.messenger.TeleBetaFreemium;\n"
    icon_anchor = "import org.telegram.messenger.UserConfig;\n"
    if icon_import not in icon_source:
        if icon_source.count(icon_anchor) != 1:
            raise SystemExit("Could not locate AppIconsSelectorCell import anchor.")
        icon_source = icon_source.replace(icon_anchor, icon_anchor + icon_import, 1)

    premium_icon_guard = "if (icon.premium && !UserConfig.hasPremiumOnAccounts()) {"
    premium_icon_guard_replacement = "if (icon.premium && !UserConfig.hasPremiumOnAccounts() && !TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.APP_ICONS)) {"
    if icon_source.count(premium_icon_guard) != 2:
        raise SystemExit("Expected exactly two premium icon guards; refusing to patch.")
    icon_source = icon_source.replace(premium_icon_guard, premium_icon_guard_replacement)

    visibility_guard = "if (MessagesController.getInstance(currentAccount).premiumFeaturesBlocked()) {"
    visibility_guard_replacement = "if (MessagesController.getInstance(currentAccount).premiumFeaturesBlocked() && !TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.APP_ICONS)) {"
    if icon_source.count(visibility_guard) != 1:
        raise SystemExit("Could not uniquely locate premium icon visibility guard.")
    icon_source = icon_source.replace(visibility_guard, visibility_guard_replacement, 1)
    icon_selector.write_text(icon_source, encoding="utf-8")

    # Theme/UI has no verified local Premium gate in this patch scope yet.
    # Do not bypass wallpaper-for-both or server/boost restrictions here.

    code = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
    if any(token in code for token in ("UserConfig.getInstance", "TLRPC.User", ".premium")):
        raise SystemExit("Freemium engine must not inspect Telegram account entitlement.")
    if "Tier.FREE.name()" not in source or "return false;" not in source:
        raise SystemExit("Freemium default-deny validation failed.")
    if not source.endswith("\n"):
        raise SystemExit("Freemium source must end with newline.")
