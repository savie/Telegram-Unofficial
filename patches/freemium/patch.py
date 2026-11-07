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

    # Chat themes are persisted per-dialog by ChatThemeController. In Tele-beta
    # Freemium, apply the selected theme locally and do not send
    # messages.setChatTheme to Telegram. Group/channel boost checks remain upstream.
    chat_theme = ROOT / "TMessagesProj/src/main/java/org/telegram/ui/Components/ChatThemeBottomSheet.java"
    chat_theme_source = chat_theme.read_text(encoding="utf-8")
    chat_theme_import = "import org.telegram.messenger.TeleBetaFreemium;\n"
    chat_theme_anchor = "import org.telegram.messenger.ChatThemeController;\n"
    if chat_theme_import not in chat_theme_source:
        if chat_theme_source.count(chat_theme_anchor) != 1:
            raise SystemExit("Could not locate ChatThemeBottomSheet import anchor.")
        chat_theme_source = chat_theme_source.replace(chat_theme_anchor, chat_theme_anchor + chat_theme_import, 1)

    apply_theme_call = "ChatThemeController.getInstance(currentAccount).setDialogTheme(chatActivity.getDialogId(), tlChatTheme, true);"
    local_apply_call = """boolean teleBetaLocalTheme = TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.CHAT_CUSTOMIZATION);
            ChatThemeController.getInstance(currentAccount).setDialogTheme(chatActivity.getDialogId(), tlChatTheme, !teleBetaLocalTheme);"""
    if chat_theme_source.count(apply_theme_call) != 1:
        raise SystemExit("Could not uniquely locate ChatThemeBottomSheet theme-apply call.")
    chat_theme_source = chat_theme_source.replace(apply_theme_call, local_apply_call, 1)
    chat_theme.write_text(chat_theme_source, encoding="utf-8")



    # Theme editor and accent customization already have local serializers in
    # Theme.java. Keep those writes, but prevent the final-save hook from
    # uploading a Tele-beta-only theme to Telegram.
    theme_file = ROOT / "TMessagesProj/src/main/java/org/telegram/ui/ActionBar/Theme.java"
    theme_source = theme_file.read_text(encoding="utf-8")
    theme_import = "import org.telegram.messenger.TeleBetaFreemium;\n"
    theme_anchor = "import org.telegram.messenger.MessagesController;\n"
    if theme_import not in theme_source:
        if theme_source.count(theme_anchor) != 1:
            raise SystemExit("Could not locate Theme.java import anchor.")
        theme_source = theme_source.replace(theme_anchor, theme_anchor + theme_import, 1)

    remote_theme_save = "if (finalSave) {\n            MessagesController.getInstance(themeInfo.account).saveThemeToServer(themeInfo, themeInfo.getAccent(false));\n        }"
    local_theme_save = "if (finalSave && !TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.CUSTOM_THEMES)) {\n            MessagesController.getInstance(themeInfo.account).saveThemeToServer(themeInfo, themeInfo.getAccent(false));\n        }"
    if theme_source.count(remote_theme_save) != 1:
        raise SystemExit("Could not uniquely locate Theme.saveCurrentTheme remote-save hook.")
    theme_source = theme_source.replace(remote_theme_save, local_theme_save, 1)
    theme_file.write_text(theme_source, encoding="utf-8")

    # Personal wallpaper (dialogId == 0) is stored in the active local theme.
    # Do not upload it as the account wallpaper for Tele-beta Freemium.
    wallpaper_file = ROOT / "TMessagesProj/src/main/java/org/telegram/ui/ThemePreviewActivity.java"
    wallpaper_source = wallpaper_file.read_text(encoding="utf-8")
    wallpaper_import = "import org.telegram.messenger.TeleBetaFreemium;\n"
    wallpaper_anchor = "import org.telegram.messenger.MessagesController;\n"
    if wallpaper_import not in wallpaper_source:
        if wallpaper_source.count(wallpaper_anchor) != 1:
            raise SystemExit("Could not locate ThemePreviewActivity import anchor.")
        wallpaper_source = wallpaper_source.replace(wallpaper_anchor, wallpaper_anchor + wallpaper_import, 1)

    remote_wallpaper_save = "MessagesController.getInstance(currentAccount).saveWallpaperToServer(path, wallpaperInfo, slug != null && dialogId == 0, 0);"
    local_wallpaper_save = """boolean teleBetaLocalPersonalWallpaper = dialogId == 0 && TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.CUSTOM_THEMES);
        if (!teleBetaLocalPersonalWallpaper) {
            MessagesController.getInstance(currentAccount).saveWallpaperToServer(path, wallpaperInfo, slug != null && dialogId == 0, 0);
        }"""
    if wallpaper_source.count(remote_wallpaper_save) != 1:
        raise SystemExit("Could not uniquely locate wallpaper server-save call.")
    wallpaper_source = wallpaper_source.replace(remote_wallpaper_save, local_wallpaper_save, 1)

    local_wallpaper_apply = "Theme.getActiveTheme().setOverrideWallpaper(wallpaperInfo);\n                Theme.reloadWallpaper(true);"
    persistent_wallpaper_apply = """Theme.getActiveTheme().setOverrideWallpaper(wallpaperInfo);
                Theme.reloadWallpaper(true);
                if (teleBetaLocalPersonalWallpaper) {
                    Theme.saveCurrentTheme(Theme.getActiveTheme(), false, false, false);
                }"""
    if wallpaper_source.count(local_wallpaper_apply) != 1:
        raise SystemExit("Could not uniquely locate local personal wallpaper apply block.")
    wallpaper_source = wallpaper_source.replace(local_wallpaper_apply, persistent_wallpaper_apply, 1)
    wallpaper_file.write_text(wallpaper_source, encoding="utf-8")



    # Theme accent editor is device-local for Tele-beta Freemium. Telegram's
    # server color/wallpaper-for-both gates are deliberately kept unchanged.
    accent_file = ROOT / "TMessagesProj/src/main/java/org/telegram/ui/ThemePreviewActivity.java"
    accent_source = accent_file.read_text(encoding="utf-8")
    accent_import = "import org.telegram.messenger.TeleBetaFreemium;\n"
    accent_import_anchor = "import org.telegram.messenger.MessagesController;\n"
    if accent_import not in accent_source:
        if accent_source.count(accent_import_anchor) != 1:
            raise SystemExit("Could not uniquely locate ThemePreviewActivity accent import anchor.")
        accent_source = accent_source.replace(accent_import_anchor, accent_import_anchor + accent_import, 1)

    accent_apply_anchor = """                if (accent != null) {
                    saveAccentWallpaper();
                    Theme.saveThemeAccents(applyingTheme, true, false, false, false);
                    Theme.clearPreviousTheme();"""
    accent_apply_local = """                if (accent != null) {
                    saveAccentWallpaper();
                    boolean telebetaLocalAccent = screenType == SCREEN_TYPE_ACCENT_COLOR && TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.CUSTOM_THEMES);
                    Theme.saveThemeAccents(applyingTheme, true, false, false, false);
                    Theme.clearPreviousTheme();"""
    if accent_source.count(accent_apply_anchor) != 1:
        raise SystemExit("Could not uniquely locate ThemePreviewActivity accent apply/save block.")
    accent_source = accent_source.replace(accent_apply_anchor, accent_apply_local, 1)

    accent_save_menu_anchor = """                    Theme.saveThemeAccents(applyingTheme, true, false, false, true);
                    Theme.applyPreviousTheme();"""
    accent_save_menu_local = """                    boolean telebetaLocalAccent = TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.CUSTOM_THEMES);
                    Theme.saveThemeAccents(applyingTheme, true, false, false, !telebetaLocalAccent);
                    Theme.applyPreviousTheme();"""
    if accent_source.count(accent_save_menu_anchor) != 1:
        raise SystemExit("Could not uniquely locate ThemePreviewActivity accent wallpaper save block.")
    accent_source = accent_source.replace(accent_save_menu_anchor, accent_save_menu_local, 1)

    accent_file.write_text(accent_source, encoding="utf-8")

    # Local-only profile/name colors for the current Tele-beta account.
    # These preferences intentionally never issue TL_account.updateColor.
    local_style = ROOT / "TMessagesProj/src/main/java/org/telegram/messenger/TeleBetaLocalProfileStyle.java"
    local_style_source = """package org.telegram.messenger;

import android.content.Context;
import android.content.SharedPreferences;
import org.telegram.tgnet.TLRPC;
import java.util.ArrayList;

public final class TeleBetaLocalProfileStyle {
    private static final String PREFS = "telebeta_local_profile_style";
    private static final String NAME_COLOR = "name_color_";
    private static final String PROFILE_COLOR = "profile_color_";
    private static final String PROFILE_EMOJI = "profile_emoji_";
    private static final String NAME_COLLECTIBLE = "name_collectible_";
    private static final String PROFILE_COLLECTIBLE = "profile_collectible_";

    private TeleBetaLocalProfileStyle() {}

    private static SharedPreferences prefs(int account) {
        return ApplicationLoader.applicationContext.getSharedPreferences(PREFS + "_" + account, Context.MODE_PRIVATE);
    }

    private static boolean isCurrentUser(TLRPC.User user) {
        if (user == null) return false;
        int account = UserConfig.selectedAccount;
        return UserConfig.getInstance(account).getClientUserId() == user.id
            && TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.CUSTOM_UI);
    }

    private static String listToString(ArrayList<Integer> values) {
        if (values == null || values.isEmpty()) return "";
        StringBuilder out = new StringBuilder();
        for (int i = 0; i < values.size(); i++) {
            if (i > 0) out.append(',');
            out.append(values.get(i));
        }
        return out.toString();
    }

    private static ArrayList<Integer> stringToList(String value) {
        ArrayList<Integer> out = new ArrayList<>();
        if (value == null || value.isEmpty()) return out;
        for (String part : value.split(",")) {
            try { out.add(Integer.parseInt(part)); } catch (Exception ignored) {}
        }
        return out;
    }

    public static TLRPC.TL_peerColorCollectible getNameCollectible(TLRPC.User user) {
        if (!isCurrentUser(user)) return null;
        SharedPreferences p = prefs(UserConfig.selectedAccount);
        String prefix = NAME_COLLECTIBLE + user.id + "_";
        if (!p.getBoolean(prefix + "present", false)) return null;
        TLRPC.TL_peerColorCollectible value = new TLRPC.TL_peerColorCollectible();
        value.collectible_id = p.getLong(prefix + "id", 0);
        value.gift_emoji_id = p.getLong(prefix + "gift_emoji", 0);
        value.background_emoji_id = p.getLong(prefix + "background_emoji", 0);
        value.accent_color = p.getInt(prefix + "accent", 0);
        value.colors = stringToList(p.getString(prefix + "colors", ""));
        if (p.contains(prefix + "dark_accent")) {
            value.flags |= 1;
            value.dark_accent_color = p.getInt(prefix + "dark_accent", 0);
        }
        if (p.contains(prefix + "dark_colors")) {
            value.flags |= 2;
            value.dark_colors = stringToList(p.getString(prefix + "dark_colors", ""));
        }
        return value;
    }

    public static TLRPC.TL_emojiStatusCollectible getProfileCollectible(TLRPC.User user) {
        if (!isCurrentUser(user)) return null;
        SharedPreferences p = prefs(UserConfig.selectedAccount);
        String prefix = PROFILE_COLLECTIBLE + user.id + "_";
        if (!p.getBoolean(prefix + "present", false)) return null;
        TLRPC.TL_emojiStatusCollectible value = new TLRPC.TL_emojiStatusCollectible();
        value.collectible_id = p.getLong(prefix + "id", 0);
        value.document_id = p.getLong(prefix + "document", 0);
        value.title = p.getString(prefix + "title", "");
        value.slug = p.getString(prefix + "slug", "");
        value.pattern_document_id = p.getLong(prefix + "pattern", 0);
        value.center_color = p.getInt(prefix + "center", 0);
        value.edge_color = p.getInt(prefix + "edge", 0);
        value.pattern_color = p.getInt(prefix + "pattern_color", 0);
        value.text_color = p.getInt(prefix + "text", 0);
        return value;
    }

    public static int getNameColor(TLRPC.User user, int fallback) {
        if (!isCurrentUser(user)) return fallback;
        if (getNameCollectible(user) != null) return -1;
        return prefs(UserConfig.selectedAccount).getInt(NAME_COLOR + user.id, fallback);
    }

    public static int getProfileColor(TLRPC.User user, int fallback) {
        if (!isCurrentUser(user)) return fallback;
        if (getProfileCollectible(user) != null) return -1;
        return prefs(UserConfig.selectedAccount).getInt(PROFILE_COLOR + user.id, fallback);
    }

    public static long getProfileEmoji(TLRPC.User user, long fallback) {
        if (!isCurrentUser(user)) return fallback;
        TLRPC.TL_emojiStatusCollectible collectible = getProfileCollectible(user);
        if (collectible != null) return collectible.pattern_document_id;
        SharedPreferences p = prefs(UserConfig.selectedAccount);
        return p.getLong(PROFILE_EMOJI + user.id, fallback);
    }

    public static long getProfileCollectibleId(TLRPC.User user, long fallback) {
        TLRPC.TL_emojiStatusCollectible collectible = getProfileCollectible(user);
        return collectible == null ? fallback : collectible.collectible_id;
    }

    public static void save(int account, long userId, int nameColor, int profileColor, long profileEmoji,
                            TLRPC.TL_peerColorCollectible nameCollectible,
                            TLRPC.TL_emojiStatusCollectible profileCollectible) {
        SharedPreferences.Editor edit = prefs(account).edit()
            .putInt(NAME_COLOR + userId, nameColor)
            .putInt(PROFILE_COLOR + userId, profileColor)
            .putLong(PROFILE_EMOJI + userId, profileEmoji);
        String namePrefix = NAME_COLLECTIBLE + userId + "_";
        if (nameCollectible != null) {
            edit.putBoolean(namePrefix + "present", true)
                .putLong(namePrefix + "id", nameCollectible.collectible_id)
                .putLong(namePrefix + "gift_emoji", nameCollectible.gift_emoji_id)
                .putLong(namePrefix + "background_emoji", nameCollectible.background_emoji_id)
                .putInt(namePrefix + "accent", nameCollectible.accent_color)
                .putString(namePrefix + "colors", listToString(nameCollectible.colors));
            if ((nameCollectible.flags & 1) != 0) edit.putInt(namePrefix + "dark_accent", nameCollectible.dark_accent_color);
            else edit.remove(namePrefix + "dark_accent");
            if ((nameCollectible.flags & 2) != 0) edit.putString(namePrefix + "dark_colors", listToString(nameCollectible.dark_colors));
            else edit.remove(namePrefix + "dark_colors");
        } else {
            edit.remove(namePrefix + "present").remove(namePrefix + "id").remove(namePrefix + "gift_emoji")
                .remove(namePrefix + "background_emoji").remove(namePrefix + "accent").remove(namePrefix + "colors")
                .remove(namePrefix + "dark_accent").remove(namePrefix + "dark_colors");
        }
        String profilePrefix = PROFILE_COLLECTIBLE + userId + "_";
        if (profileCollectible != null) {
            edit.putBoolean(profilePrefix + "present", true)
                .putLong(profilePrefix + "id", profileCollectible.collectible_id)
                .putLong(profilePrefix + "document", profileCollectible.document_id)
                .putString(profilePrefix + "title", profileCollectible.title)
                .putString(profilePrefix + "slug", profileCollectible.slug)
                .putLong(profilePrefix + "pattern", profileCollectible.pattern_document_id)
                .putInt(profilePrefix + "center", profileCollectible.center_color)
                .putInt(profilePrefix + "edge", profileCollectible.edge_color)
                .putInt(profilePrefix + "pattern_color", profileCollectible.pattern_color)
                .putInt(profilePrefix + "text", profileCollectible.text_color);
        } else {
            edit.remove(profilePrefix + "present").remove(profilePrefix + "id").remove(profilePrefix + "document")
                .remove(profilePrefix + "title").remove(profilePrefix + "slug").remove(profilePrefix + "pattern")
                .remove(profilePrefix + "center").remove(profilePrefix + "edge").remove(profilePrefix + "pattern_color")
                .remove(profilePrefix + "text");
        }
        edit.commit();
    }
}
"""
    local_style.parent.mkdir(parents=True, exist_ok=True)
    local_style.write_text(local_style_source, encoding="utf-8")

    user_object = ROOT / "TMessagesProj/src/main/java/org/telegram/messenger/UserObject.java"
    user_source = user_object.read_text(encoding="utf-8")
    name_getter = "public static int getColorId(TLRPC.User user) {"
    profile_getter = "public static int getProfileColorId(TLRPC.User user) {"
    name_fallback = """        if (user == null) return 0;
        if (user.color instanceof TLRPC.TL_peerColor && (user.color.flags & 1) != 0) return user.color.color;
        return (int) (user.id % 7);"""
    name_local = """        if (user == null) return 0;
        TLRPC.TL_peerColorCollectible localCollectible = TeleBetaLocalProfileStyle.getNameCollectible(user);
        if (localCollectible != null) {
            user.color = localCollectible;
            return -1;
        }
        int fallback = user.color instanceof TLRPC.TL_peerColor && (user.color.flags & 1) != 0 ? user.color.color : (int) (user.id % 7);
        return TeleBetaLocalProfileStyle.getNameColor(user, fallback);"""
    profile_fallback = """        if (user == null) return 0;
        if (user.profile_color instanceof TLRPC.TL_peerColor && (user.profile_color.flags & 1) != 0) return user.profile_color.color;
        return -1;"""
    profile_local = """        if (user == null) return 0;
        TLRPC.TL_emojiStatusCollectible localCollectible = TeleBetaLocalProfileStyle.getProfileCollectible(user);
        if (localCollectible != null) {
            user.emoji_status = localCollectible;
            return -1;
        }
        int fallback = user.profile_color instanceof TLRPC.TL_peerColor && (user.profile_color.flags & 1) != 0 ? user.profile_color.color : -1;
        return TeleBetaLocalProfileStyle.getProfileColor(user, fallback);"""
    if user_source.count(name_getter) != 1 or user_source.count(name_fallback) != 1:
        raise SystemExit("Could not uniquely locate UserObject name-color getter.")
    if user_source.count(profile_getter) != 1 or user_source.count(profile_fallback) != 1:
        raise SystemExit("Could not uniquely locate UserObject profile-color getter.")
    user_source = user_source.replace(name_fallback, name_local, 1)
    user_source = user_source.replace(profile_fallback, profile_local, 1)

    profile_emoji_getter = """    public static long getProfileEmojiId(TLRPC.User user) {
        if (user != null && user.emoji_status instanceof TLRPC.TL_emojiStatusCollectible) {
            return ((TLRPC.TL_emojiStatusCollectible) user.emoji_status).pattern_document_id;
        }
        if (user != null && user.profile_color != null && (user.profile_color.flags & 2) != 0) return user.profile_color.background_emoji_id;
        return 0;
    }"""
    profile_emoji_local = """    public static long getProfileEmojiId(TLRPC.User user) {
        TLRPC.TL_emojiStatusCollectible localCollectible = TeleBetaLocalProfileStyle.getProfileCollectible(user);
        if (localCollectible != null) {
            user.emoji_status = localCollectible;
            return localCollectible.pattern_document_id;
        }
        if (user != null && user.emoji_status instanceof TLRPC.TL_emojiStatusCollectible) {
            return ((TLRPC.TL_emojiStatusCollectible) user.emoji_status).pattern_document_id;
        }
        long fallback = user != null && user.profile_color != null && (user.profile_color.flags & 2) != 0 ? user.profile_color.background_emoji_id : 0;
        return TeleBetaLocalProfileStyle.getProfileEmoji(user, fallback);
    }"""
    only_profile_emoji_getter = """    public static long getOnlyProfileEmojiId(TLRPC.User user) {
        if (user != null && user.profile_color instanceof TLRPC.TL_peerColor && (user.profile_color.flags & 2) != 0) return user.profile_color.background_emoji_id;
        return 0;
    }"""
    only_profile_emoji_local = """    public static long getOnlyProfileEmojiId(TLRPC.User user) {
        if (TeleBetaLocalProfileStyle.getProfileCollectible(user) != null) return 0;
        long fallback = user != null && user.profile_color instanceof TLRPC.TL_peerColor && (user.profile_color.flags & 2) != 0 ? user.profile_color.background_emoji_id : 0;
        return TeleBetaLocalProfileStyle.getProfileEmoji(user, fallback);
    }"""
    profile_collectible_getter = """    public static long getProfileCollectibleId(TLRPC.User user) {
        if (user != null && user.emoji_status instanceof TLRPC.TL_emojiStatusCollectible) {
            return ((TLRPC.TL_emojiStatusCollectible) user.emoji_status).collectible_id;
        }
        return 0;
    }"""
    profile_collectible_local = """    public static long getProfileCollectibleId(TLRPC.User user) {
        long fallback = user != null && user.emoji_status instanceof TLRPC.TL_emojiStatusCollectible ? ((TLRPC.TL_emojiStatusCollectible) user.emoji_status).collectible_id : 0;
        return TeleBetaLocalProfileStyle.getProfileCollectibleId(user, fallback);
    }"""
    if user_source.count(profile_emoji_getter) != 1 or user_source.count(only_profile_emoji_getter) != 1 or user_source.count(profile_collectible_getter) != 1:
        raise SystemExit("Could not uniquely locate UserObject profile emoji/collectible getters.")
    user_source = user_source.replace(profile_emoji_getter, profile_emoji_local, 1)
    user_source = user_source.replace(only_profile_emoji_getter, only_profile_emoji_local, 1)
    user_source = user_source.replace(profile_collectible_getter, profile_collectible_local, 1)

    user_object.write_text(user_source, encoding="utf-8")

    peer_file = ROOT / "TMessagesProj/src/main/java/org/telegram/ui/PeerColorActivity.java"
    peer_source = peer_file.read_text(encoding="utf-8")
    peer_import_anchor = "import org.telegram.messenger.UserConfig;\n"
    peer_import = "import org.telegram.messenger.TeleBetaFreemium;\nimport org.telegram.messenger.TeleBetaLocalProfileStyle;\n"
    if peer_import not in peer_source:
        if peer_source.count(peer_import_anchor) != 1:
            raise SystemExit("Could not locate PeerColorActivity import anchor.")
        peer_source = peer_source.replace(peer_import_anchor, peer_import_anchor + peer_import, 1)

    locked_button = "!getUserConfig().isPremium() && !isChannel ? buttonLocked"
    unlocked_button = "!getUserConfig().isPremium() && !isChannel && !isTeleBetaLocalProfileStyleEnabled() ? buttonLocked"
    if peer_source.count(locked_button) != 1:
        raise SystemExit("Could not uniquely locate profile-style locked button state.")
    peer_source = peer_source.replace(locked_button, unlocked_button, 1)

    setup_guard = "        public void setupValues() {"
    setup_method = """        public void setupValues() {"""
    if peer_source.count(setup_guard) != 1:
        raise SystemExit("Could not uniquely locate PeerColorActivity Page.setupValues.")

    setup_profile_anchor = """                    selectedEmojiCollectible = user != null && user.emoji_status instanceof TLRPC.TL_emojiStatusCollectible ? (TLRPC.TL_emojiStatusCollectible) user.emoji_status : null;
                    selectedPeerCollectible = null;"""
    setup_profile_local = """                    TLRPC.TL_emojiStatusCollectible localCollectible = TeleBetaLocalProfileStyle.getProfileCollectible(user);
                    selectedEmojiCollectible = localCollectible != null ? localCollectible : (user != null && user.emoji_status instanceof TLRPC.TL_emojiStatusCollectible ? (TLRPC.TL_emojiStatusCollectible) user.emoji_status : null);
                    selectedPeerCollectible = null;"""
    setup_name_anchor = """                    selectedEmojiCollectible = null;
                    selectedPeerCollectible = user != null && user.color instanceof TLRPC.TL_peerColorCollectible ? (TLRPC.TL_peerColorCollectible) user.color : null;"""
    setup_name_local = """                    selectedEmojiCollectible = null;
                    TLRPC.TL_peerColorCollectible localNameCollectible = TeleBetaLocalProfileStyle.getNameCollectible(user);
                    selectedPeerCollectible = localNameCollectible != null ? localNameCollectible : (user != null && user.color instanceof TLRPC.TL_peerColorCollectible ? (TLRPC.TL_peerColorCollectible) user.color : null);"""
    if peer_source.count(setup_profile_anchor) != 1 or peer_source.count(setup_name_anchor) != 1:
        raise SystemExit("Could not uniquely locate local profile collectible restore anchors.")
    peer_source = peer_source.replace(setup_profile_anchor, setup_profile_local, 1)
    peer_source = peer_source.replace(setup_name_anchor, setup_name_local, 1)

    local_button_anchor = """    private void buttonClick() {
        if (loading) {
            return;
        }
        if (isChannel) {"""
    local_button_code = """    private void buttonClick() {
        if (loading) {
            return;
        }
        if (isTeleBetaLocalProfileStyleEnabled()) {
            apply();
            finishFragment();
            showBulletin();
            return;
        }
        if (isChannel) {"""
    if peer_source.count(local_button_anchor) != 1:
        raise SystemExit("Could not uniquely locate local profile style button click insertion point.")
    peer_source = peer_source.replace(local_button_anchor, local_button_code, 1)

    # UserObject getters transparently overlay persisted local colors for the current account.

    click_guard = "if (!getUserConfig().isPremium()) {"
    click_guard_local = "if (!getUserConfig().isPremium() && !isTeleBetaLocalProfileStyleEnabled()) {"
    if peer_source.count(click_guard) != 1:
        raise SystemExit("Could not uniquely locate profile-style Premium click guard.")
    peer_source = peer_source.replace(click_guard, click_guard_local, 1)

    apply_guard = "if (applying || !isChannel && !getUserConfig().isPremium()) {"
    apply_guard_local = "if (applying || !isChannel && !getUserConfig().isPremium() && !isTeleBetaLocalProfileStyleEnabled()) {"
    if peer_source.count(apply_guard) != 1:
        raise SystemExit("Could not uniquely locate profile-style apply guard.")
    peer_source = peer_source.replace(apply_guard, apply_guard_local, 1)

    button_state_anchor = """        public void updateButton(boolean animated) {
            if (selectedResaleGift != null) {"""
    button_state_local = """        public void updateButton(boolean animated) {
            if (selectedResaleGift != null && !isTeleBetaLocalProfileStyleEnabled()) {"""
    if peer_source.count(button_state_anchor) != 1:
        raise SystemExit("Could not uniquely locate local collectible apply button label.")
    peer_source = peer_source.replace(button_state_anchor, button_state_local, 1)

    apply_user_anchor = """            final TLRPC.User me = getUserConfig().getCurrentUser();
            if (me.color == null) {"""
    apply_user_local = """            final TLRPC.User me = getUserConfig().getCurrentUser();
            if (isTeleBetaLocalProfileStyleEnabled()) {
                TeleBetaLocalProfileStyle.save(currentAccount, me.id, namePage.selectedColor, profilePage.selectedColor, profilePage.selectedEmoji, namePage.selectedPeerCollectible, profilePage.selectedEmojiCollectible);
                NotificationCenter.getInstance(currentAccount).postNotificationName(NotificationCenter.updateInterfaces, MessagesController.UPDATE_MASK_NAME | MessagesController.UPDATE_MASK_AVATAR);
                return;
            }
            if (me.color == null) {"""
    if peer_source.count(apply_user_anchor) != 1:
        raise SystemExit("Could not uniquely locate profile-style apply block.")
    peer_source = peer_source.replace(apply_user_anchor, apply_user_local, 1)

    helper_anchor = "    private boolean applyingName, applyingProfile;"
    helper_methods = """    private boolean isTeleBetaLocalProfileStyleEnabled() {
        return !isChannel && TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.CUSTOM_UI);
    }

    private boolean applyingName, applyingProfile;"""
    if peer_source.count(helper_anchor) != 1:
        raise SystemExit("Could not uniquely locate profile-style helper insertion point.")
    peer_source = peer_source.replace(helper_anchor, helper_methods, 1)
    peer_file.write_text(peer_source, encoding="utf-8")


    profile_activity = ROOT / "TMessagesProj/src/main/java/org/telegram/ui/ProfileActivity.java"
    profile_activity_source = profile_activity.read_text(encoding="utf-8")
    profile_style_import = "import org.telegram.messenger.TeleBetaLocalProfileStyle;\n"
    profile_style_import_anchor = "import org.telegram.messenger.UserObject;\n"
    if profile_style_import not in profile_activity_source:
        if profile_activity_source.count(profile_style_import_anchor) != 1:
            raise SystemExit("Could not locate ProfileActivity local collectible import anchor.")
        profile_activity_source = profile_activity_source.replace(profile_style_import_anchor, profile_style_import_anchor + profile_style_import, 1)
    profile_peer_color_anchor = "            peerColor = MessagesController.PeerColor.fromCollectible(user.emoji_status);"
    profile_peer_color_local = """            TLRPC.TL_emojiStatusCollectible teleBetaLocalCollectible = TeleBetaLocalProfileStyle.getProfileCollectible(user);
            if (teleBetaLocalCollectible != null) user.emoji_status = teleBetaLocalCollectible;
            peerColor = MessagesController.PeerColor.fromCollectible(user.emoji_status);"""
    if profile_activity_source.count(profile_peer_color_anchor) != 1:
        raise SystemExit("Could not uniquely locate ProfileActivity collectible peer-color rendering.")
    profile_activity_source = profile_activity_source.replace(profile_peer_color_anchor, profile_peer_color_local, 1)
    profile_activity.write_text(profile_activity_source, encoding="utf-8")


    
    # Guard negative local collectible color IDs before upstream array lookups.
    safe_color_patches = [
        (
            ROOT / "TMessagesProj/src/main/java/org/telegram/ui/Components/Paint/Views/LinkPreview.java",
            "            previewPaint.setColor(color == null ? Theme.getColor(Theme.keys_avatar_nameInMessage[colorId % Theme.keys_avatar_nameInMessage.length]) : color.getColor1());",
            "            previewPaint.setColor(color == null ? Theme.getColor(Theme.keys_avatar_nameInMessage[colorId >= 0 ? colorId % Theme.keys_avatar_nameInMessage.length : 0]) : color.getColor1());",
        ),
        (
            ROOT / "TMessagesProj/src/main/java/org/telegram/ui/Components/ReplyMessageLine.java",
            "        if (colorId < 7) {\\n            color1 = color2 = color3 = Theme.getColor(Theme.keys_avatar_nameInMessage[colorId], resourcesProvider);",
            "        if (colorId < 0) {\\n            colorId = 0;\\n        }\\n        if (colorId < 7) {\\n            color1 = color2 = color3 = Theme.getColor(Theme.keys_avatar_nameInMessage[colorId], resourcesProvider);",
        ),
        (
            ROOT / "TMessagesProj/src/main/java/org/telegram/ui/PeerColorActivity.java",
            "                int colorId = UserObject.getColorId(user);\\n                if (colorId < 7) {\\n                    color = Theme.getColor(userTextColorKey = Theme.keys_avatar_nameInMessage[colorId], resourcesProvider);",
            "                int colorId = UserObject.getColorId(user);\\n                if (colorId < 0) {\\n                    colorId = 0;\\n                }\\n                if (colorId < 7) {\\n                    color = Theme.getColor(userTextColorKey = Theme.keys_avatar_nameInMessage[colorId], resourcesProvider);",
        ),
        (
            ROOT / "TMessagesProj/src/main/java/org/telegram/ui/Components/Premium/boosts/cells/msg/GiveawayResultsMessageCell.java",
            "        if (colorId < 7) {\\n            color = Theme.getColor(Theme.keys_avatar_nameInMessage[colorId], resourcesProvider);",
            "        if (colorId < 0) {\\n            colorId = 0;\\n        }\\n        if (colorId < 7) {\\n            color = Theme.getColor(Theme.keys_avatar_nameInMessage[colorId], resourcesProvider);",
        ),
        (
            ROOT / "TMessagesProj/src/main/java/org/telegram/ui/Components/Forum/MessageTopicButton.java",
            "            if (colorId < 7) {\\n                topicNameColor = getThemedColor(Theme.keys_avatar_nameInMessage[colorId]);",
            "            if (colorId < 0) {\\n                colorId = 0;\\n            }\\n            if (colorId < 7) {\\n                topicNameColor = getThemedColor(Theme.keys_avatar_nameInMessage[colorId]);",
        ),
        (
            ROOT / "TMessagesProj/src/main/java/org/telegram/ui/Components/Premium/boosts/cells/msg/GiveawayMessageCell.java",
            "        if (colorId < 7) {\\n            color = Theme.getColor(Theme.keys_avatar_nameInMessage[colorId], resourcesProvider);",
            "        if (colorId < 0) {\\n            colorId = 0;\\n        }\\n        if (colorId < 7) {\\n            color = Theme.getColor(Theme.keys_avatar_nameInMessage[colorId], resourcesProvider);",
        ),
    ]
    for file_path, old_snippet, new_snippet in safe_color_patches:
        source_text = file_path.read_text(encoding="utf-8")
        old_snippet = old_snippet.replace("\\\\n", "\\n")
        new_snippet = new_snippet.replace("\\\\n", "\\n")
        if source_text.count(old_snippet) != 1:
            raise SystemExit(f"Could not uniquely locate negative color guard in {file_path.name}.")
        file_path.write_text(source_text.replace(old_snippet, new_snippet, 1), encoding="utf-8")






    # Local emoji discovery: enable suggestions and preview/install controls for
    # emoji packs in Tele-beta. Sending premium emoji/status remains server-gated.
    suggest_file = ROOT / "TMessagesProj/src/main/java/org/telegram/ui/Components/SuggestEmojiView.java"
    suggest_source = suggest_file.read_text(encoding="utf-8")
    suggest_import = "import org.telegram.messenger.TeleBetaFreemium;\n"
    suggest_anchor = "import org.telegram.messenger.UserConfig;\n"
    if suggest_import not in suggest_source:
        if suggest_source.count(suggest_anchor) != 1:
            raise SystemExit("Could not locate SuggestEmojiView Freemium import anchor.")
        suggest_source = suggest_source.replace(suggest_anchor, suggest_anchor + suggest_import, 1)
    suggest_gate = re.compile(r"SharedConfig\.suggestAnimatedEmoji\s*&&\s*UserConfig\.getInstance\(currentAccount\)\.isPremium\(\)")
    suggest_local_gate = "SharedConfig.suggestAnimatedEmoji && (UserConfig.getInstance(currentAccount).isPremium() || TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.CUSTOM_UI))"
    suggest_source, suggest_matches = suggest_gate.subn(suggest_local_gate, suggest_source, count=1)
    if suggest_matches != 1:
        raise SystemExit("Could not locate SuggestEmojiView animated emoji suggestion gate (regex).")
    suggest_file.write_text(suggest_source, encoding="utf-8")

    adapter_file = ROOT / "TMessagesProj/src/main/java/org/telegram/ui/Adapters/StickersAdapter.java"
    adapter_source = adapter_file.read_text(encoding="utf-8")
    adapter_import = "import org.telegram.messenger.TeleBetaFreemium;\n"
    adapter_anchor = "import org.telegram.messenger.UserConfig;\n"
    if adapter_import not in adapter_source:
        if adapter_source.count(adapter_anchor) != 1:
            raise SystemExit("Could not locate StickersAdapter Freemium import anchor.")
        adapter_source = adapter_source.replace(adapter_anchor, adapter_anchor + adapter_import, 1)
    adapter_gate = "SharedConfig.suggestAnimatedEmoji && UserConfig.getInstance(currentAccount).isPremium()"
    adapter_local_gate = "SharedConfig.suggestAnimatedEmoji && (UserConfig.getInstance(currentAccount).isPremium() || TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.CUSTOM_UI))"
    if adapter_source.count(adapter_gate) != 1:
        raise SystemExit("Could not uniquely locate StickersAdapter animated emoji suggestion gate.")
    adapter_source = adapter_source.replace(adapter_gate, adapter_local_gate, 1)
    adapter_file.write_text(adapter_source, encoding="utf-8")

    sticker_alert = ROOT / "TMessagesProj/src/main/java/org/telegram/ui/Components/StickersAlert.java"
    sticker_source = sticker_alert.read_text(encoding="utf-8")
    sticker_import = "import org.telegram.messenger.TeleBetaFreemium;\n"
    sticker_anchor = "import org.telegram.messenger.UserConfig;\n"
    if sticker_import not in sticker_source:
        if sticker_source.count(sticker_anchor) != 1:
            raise SystemExit("Could not locate StickersAlert Freemium import anchor.")
        sticker_source = sticker_source.replace(sticker_anchor, sticker_anchor + sticker_import, 1)
    filter_anchor = """    private void checkPremiumStickers() {
        if (stickerSet != null) {
            stickerSet = MessagesController.getInstance(currentAccount).filterPremiumStickers(stickerSet);"""
    filter_local = """    private void checkPremiumStickers() {
        if (stickerSet != null && !TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.CUSTOM_UI)) {
            stickerSet = MessagesController.getInstance(currentAccount).filterPremiumStickers(stickerSet);"""
    if sticker_source.count(filter_anchor) != 1:
        raise SystemExit("Could not uniquely locate StickersAlert premium pack filtering.")
    sticker_source = sticker_source.replace(filter_anchor, filter_local, 1)
    pack_gate = "stickerSet.set.emojis && !UserConfig.getInstance(currentAccount).isPremium() && customButtonDelegate == null"
    pack_local_gate = "stickerSet.set.emojis && !UserConfig.getInstance(currentAccount).isPremium() && !TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.CUSTOM_UI) && customButtonDelegate == null"
    if sticker_source.count(pack_gate) != 1:
        raise SystemExit("Could not uniquely locate StickersAlert premium emoji unlock gate.")
    sticker_source = sticker_source.replace(pack_gate, pack_local_gate, 1)
    sticker_alert.write_text(sticker_source, encoding="utf-8")

    emoji_packs_alert = ROOT / "TMessagesProj/src/main/java/org/telegram/ui/Components/EmojiPacksAlert.java"
    packs_source = emoji_packs_alert.read_text(encoding="utf-8")
    packs_import = "import org.telegram.messenger.TeleBetaFreemium;\n"
    packs_anchor = "import org.telegram.messenger.UserConfig;\n"
    if packs_import not in packs_source:
        if packs_source.count(packs_anchor) != 1:
            raise SystemExit("Could not locate EmojiPacksAlert Freemium import anchor.")
        packs_source = packs_source.replace(packs_anchor, packs_anchor + packs_import, 1)
    header_gate = "if (!UserConfig.getInstance(currentAccount).isPremium()) {"
    header_local_gate = "if (!UserConfig.getInstance(currentAccount).isPremium() && !TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.CUSTOM_UI)) {"
    if packs_source.count(header_gate) != 1:
        raise SystemExit("Could not uniquely locate EmojiPacksAlert premium header unlock gate.")
    packs_source = packs_source.replace(header_gate, header_local_gate, 1)
    row_gate = "premium && unlockButtonView != null && !UserConfig.getInstance(currentAccount).isPremium()"
    row_local_gate = "premium && unlockButtonView != null && !UserConfig.getInstance(currentAccount).isPremium() && !TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.CUSTOM_UI)"
    if packs_source.count(row_gate) != 1:
        raise SystemExit("Could not uniquely locate EmojiPacksAlert premium pack row gate.")
    packs_source = packs_source.replace(row_gate, row_local_gate, 1)
    emoji_packs_alert.write_text(packs_source, encoding="utf-8")


    code = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
    if any(token in code for token in ("UserConfig.getInstance", "TLRPC.User", ".premium")):
        raise SystemExit("Freemium engine must not inspect Telegram account entitlement.")
    if "Tier.FREE.name()" not in source or "return false;" not in source:
        raise SystemExit("Freemium default-deny validation failed.")
    if not source.endswith("\n"):
        raise SystemExit("Freemium source must end with newline.")
