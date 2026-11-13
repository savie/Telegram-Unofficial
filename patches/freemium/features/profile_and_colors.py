"""Local Name/Profile Colors and collectible overlays, stored per Telegram account."""
from pathlib import Path


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


LOCAL_PROFILE_STYLE_JAVA = r'''package org.telegram.messenger;

import android.content.Context;
import android.content.SharedPreferences;

import org.telegram.tgnet.TLRPC;

import java.util.ArrayList;

public final class TeleBetaLocalProfileStyle {
    private static final String PREFS_PREFIX = "telebeta_local_profile_style_";

    private TeleBetaLocalProfileStyle() {
    }

    private static SharedPreferences preferences(int account) {
        if (!UserConfig.isValidAccount(account) || ApplicationLoader.applicationContext == null) {
            return null;
        }
        return ApplicationLoader.applicationContext.getSharedPreferences(
            PREFS_PREFIX + account,
            Context.MODE_PRIVATE
        );
    }

    private static boolean isCurrentUser(int account, TLRPC.User user) {
        return user != null
            && UserConfig.isValidAccount(account)
            && UserConfig.getInstance(account).getClientUserId() == user.id
            && (UserConfig.getInstance(account).isPremium() || TeleBetaFreemium.isActive(account));
    }

    private static ArrayList<Integer> parseColors(String value) {
        ArrayList<Integer> colors = new ArrayList<>();
        if (value == null || value.isEmpty()) {
            return colors;
        }
        for (String item : value.split(",")) {
            try {
                colors.add(Integer.parseInt(item));
            } catch (NumberFormatException ignored) {
            }
        }
        return colors;
    }

    private static String serializeColors(ArrayList<Integer> colors) {
        if (colors == null || colors.isEmpty()) {
            return "";
        }
        StringBuilder result = new StringBuilder();
        for (int i = 0; i < colors.size(); i++) {
            if (i > 0) {
                result.append(',');
            }
            result.append(colors.get(i));
        }
        return result.toString();
    }

    public static TLRPC.TL_peerColorCollectible getNameCollectible(int account, TLRPC.User user) {
        if (!isCurrentUser(account, user)) {
            return null;
        }
        SharedPreferences prefs = preferences(account);
        String key = "name_collectible_" + user.id + "_";
        if (prefs == null || !prefs.getBoolean(key + "present", false)) {
            return null;
        }

        TLRPC.TL_peerColorCollectible collectible = new TLRPC.TL_peerColorCollectible();
        collectible.collectible_id = prefs.getLong(key + "id", 0L);
        collectible.gift_emoji_id = prefs.getLong(key + "gift_emoji_id", 0L);
        collectible.background_emoji_id = prefs.getLong(key + "background_emoji_id", 0L);
        collectible.accent_color = prefs.getInt(key + "accent_color", 0);
        collectible.colors = parseColors(prefs.getString(key + "colors", ""));
        if (prefs.contains(key + "dark_accent_color")) {
            collectible.flags |= 1;
            collectible.dark_accent_color = prefs.getInt(key + "dark_accent_color", 0);
        }
        if (prefs.contains(key + "dark_colors")) {
            collectible.flags |= 2;
            collectible.dark_colors = parseColors(prefs.getString(key + "dark_colors", ""));
        }
        return collectible;
    }

    public static TLRPC.TL_emojiStatusCollectible getProfileCollectible(int account, TLRPC.User user) {
        if (!isCurrentUser(account, user)) {
            return null;
        }
        SharedPreferences prefs = preferences(account);
        String key = "profile_collectible_" + user.id + "_";
        if (prefs == null || !prefs.getBoolean(key + "present", false)) {
            return null;
        }

        TLRPC.TL_emojiStatusCollectible collectible = new TLRPC.TL_emojiStatusCollectible();
        collectible.collectible_id = prefs.getLong(key + "id", 0L);
        collectible.document_id = prefs.getLong(key + "document_id", 0L);
        collectible.title = prefs.getString(key + "title", "");
        collectible.slug = prefs.getString(key + "slug", "");
        collectible.pattern_document_id = prefs.getLong(key + "pattern_document_id", 0L);
        collectible.center_color = prefs.getInt(key + "center_color", 0);
        collectible.edge_color = prefs.getInt(key + "edge_color", 0);
        collectible.pattern_color = prefs.getInt(key + "pattern_color", 0);
        collectible.text_color = prefs.getInt(key + "text_color", 0);
        return collectible;
    }

    public static int getNameColor(int account, TLRPC.User user, int fallback) {
        if (!isCurrentUser(account, user)) {
            return fallback;
        }
        if (getNameCollectible(account, user) != null) {
            return -1;
        }
        SharedPreferences prefs = preferences(account);
        return prefs == null ? fallback : prefs.getInt("name_color_" + user.id, fallback);
    }

    public static int getProfileColor(int account, TLRPC.User user, int fallback) {
        if (!isCurrentUser(account, user)) {
            return fallback;
        }
        if (getProfileCollectible(account, user) != null) {
            return -1;
        }
        SharedPreferences prefs = preferences(account);
        return prefs == null ? fallback : prefs.getInt("profile_color_" + user.id, fallback);
    }

    public static long getProfileEmoji(int account, TLRPC.User user, long fallback) {
        if (!isCurrentUser(account, user)) {
            return fallback;
        }
        TLRPC.TL_emojiStatusCollectible collectible = getProfileCollectible(account, user);
        if (collectible != null) {
            return collectible.pattern_document_id;
        }
        SharedPreferences prefs = preferences(account);
        return prefs == null ? fallback : prefs.getLong("profile_emoji_" + user.id, fallback);
    }

    public static long getProfileCollectibleId(int account, TLRPC.User user, long fallback) {
        TLRPC.TL_emojiStatusCollectible collectible = getProfileCollectible(account, user);
        return collectible == null ? fallback : collectible.collectible_id;
    }

    public static void save(
        int account,
        long userId,
        int nameColor,
        int profileColor,
        long profileEmoji,
        TLRPC.TL_peerColorCollectible nameCollectible,
        TLRPC.TL_emojiStatusCollectible profileCollectible
    ) {
        SharedPreferences prefs = preferences(account);
        if (prefs == null || UserConfig.getInstance(account).getClientUserId() != userId) {
            return;
        }

        SharedPreferences.Editor editor = prefs.edit()
            .putInt("name_color_" + userId, nameColor)
            .putInt("profile_color_" + userId, profileColor)
            .putLong("profile_emoji_" + userId, profileEmoji);

        String nameKey = "name_collectible_" + userId + "_";
        if (nameCollectible != null) {
            editor.putBoolean(nameKey + "present", true)
                .putLong(nameKey + "id", nameCollectible.collectible_id)
                .putLong(nameKey + "gift_emoji_id", nameCollectible.gift_emoji_id)
                .putLong(nameKey + "background_emoji_id", nameCollectible.background_emoji_id)
                .putInt(nameKey + "accent_color", nameCollectible.accent_color)
                .putString(nameKey + "colors", serializeColors(nameCollectible.colors));
            if ((nameCollectible.flags & 1) != 0) {
                editor.putInt(nameKey + "dark_accent_color", nameCollectible.dark_accent_color);
            } else {
                editor.remove(nameKey + "dark_accent_color");
            }
            if ((nameCollectible.flags & 2) != 0) {
                editor.putString(nameKey + "dark_colors", serializeColors(nameCollectible.dark_colors));
            } else {
                editor.remove(nameKey + "dark_colors");
            }
        } else {
            editor.remove(nameKey + "present")
                .remove(nameKey + "id")
                .remove(nameKey + "gift_emoji_id")
                .remove(nameKey + "background_emoji_id")
                .remove(nameKey + "accent_color")
                .remove(nameKey + "colors")
                .remove(nameKey + "dark_accent_color")
                .remove(nameKey + "dark_colors");
        }

        String profileKey = "profile_collectible_" + userId + "_";
        if (profileCollectible != null) {
            editor.putBoolean(profileKey + "present", true)
                .putLong(profileKey + "id", profileCollectible.collectible_id)
                .putLong(profileKey + "document_id", profileCollectible.document_id)
                .putString(profileKey + "title", profileCollectible.title)
                .putString(profileKey + "slug", profileCollectible.slug)
                .putLong(profileKey + "pattern_document_id", profileCollectible.pattern_document_id)
                .putInt(profileKey + "center_color", profileCollectible.center_color)
                .putInt(profileKey + "edge_color", profileCollectible.edge_color)
                .putInt(profileKey + "pattern_color", profileCollectible.pattern_color)
                .putInt(profileKey + "text_color", profileCollectible.text_color);
        } else {
            editor.remove(profileKey + "present")
                .remove(profileKey + "id")
                .remove(profileKey + "document_id")
                .remove(profileKey + "title")
                .remove(profileKey + "slug")
                .remove(profileKey + "pattern_document_id")
                .remove(profileKey + "center_color")
                .remove(profileKey + "edge_color")
                .remove(profileKey + "pattern_color")
                .remove(profileKey + "text_color");
        }
        editor.apply();
    }
}
'''


def stage_local_profile_style(upstream_root: Path) -> tuple[Path, str]:
    target = upstream_root / "TMessagesProj/src/main/java/org/telegram/messenger/TeleBetaLocalProfileStyle.java"
    return target, LOCAL_PROFILE_STYLE_JAVA


def patch_user_object_profile_style(source: str) -> str:
    source = _ensure_import(
        source,
        "import org.telegram.tgnet.TLRPC;\n",
        "import org.telegram.messenger.TeleBetaLocalProfileStyle;\n",
        "UserObject",
    )
    replacements = (
        (
            """    public static int getColorId(TLRPC.User user) {
        if (user == null) return 0;
        if (user.color instanceof TLRPC.TL_peerColor && (user.color.flags & 1) != 0) return user.color.color;
        return (int) (user.id % 7);
    }""",
            """    public static int getColorId(TLRPC.User user) {
        if (user == null) return 0;
        int account = UserConfig.selectedAccount;
        TLRPC.TL_peerColorCollectible local = TeleBetaLocalProfileStyle.getNameCollectible(account, user);
        if (local != null) {
            user.color = local;
            return -1;
        }
        int fallback = user.color instanceof TLRPC.TL_peerColor && (user.color.flags & 1) != 0
            ? user.color.color : (int) (user.id % 7);
        return TeleBetaLocalProfileStyle.getNameColor(account, user, fallback);
    }""",
            "UserObject.getColorId",
        ),
        (
            """    public static int getProfileColorId(TLRPC.User user) {
        if (user == null) return 0;
        if (user.profile_color instanceof TLRPC.TL_peerColor && (user.profile_color.flags & 1) != 0) return user.profile_color.color;
        return -1;
    }""",
            """    public static int getProfileColorId(TLRPC.User user) {
        if (user == null) return 0;
        int account = UserConfig.selectedAccount;
        TLRPC.TL_emojiStatusCollectible local = TeleBetaLocalProfileStyle.getProfileCollectible(account, user);
        if (local != null) {
            user.emoji_status = local;
            return -1;
        }
        int fallback = user.profile_color instanceof TLRPC.TL_peerColor && (user.profile_color.flags & 1) != 0
            ? user.profile_color.color : -1;
        return TeleBetaLocalProfileStyle.getProfileColor(account, user, fallback);
    }""",
            "UserObject.getProfileColorId",
        ),
        (
            """    public static long getProfileEmojiId(TLRPC.User user) {
        if (user != null && user.emoji_status instanceof TLRPC.TL_emojiStatusCollectible) {
            return ((TLRPC.TL_emojiStatusCollectible) user.emoji_status).pattern_document_id;
        }
        if (user != null && user.profile_color != null && (user.profile_color.flags & 2) != 0) return user.profile_color.background_emoji_id;
        return 0;
    }""",
            """    public static long getProfileEmojiId(TLRPC.User user) {
        int account = UserConfig.selectedAccount;
        TLRPC.TL_emojiStatusCollectible local = TeleBetaLocalProfileStyle.getProfileCollectible(account, user);
        if (local != null) {
            user.emoji_status = local;
            return local.pattern_document_id;
        }
        if (user != null && user.emoji_status instanceof TLRPC.TL_emojiStatusCollectible) {
            return ((TLRPC.TL_emojiStatusCollectible) user.emoji_status).pattern_document_id;
        }
        long fallback = user != null && user.profile_color != null && (user.profile_color.flags & 2) != 0
            ? user.profile_color.background_emoji_id : 0L;
        return TeleBetaLocalProfileStyle.getProfileEmoji(account, user, fallback);
    }""",
            "UserObject.getProfileEmojiId",
        ),
        (
            """    public static long getOnlyProfileEmojiId(TLRPC.User user) {
        if (user != null && user.profile_color instanceof TLRPC.TL_peerColor && (user.profile_color.flags & 2) != 0) return user.profile_color.background_emoji_id;
        return 0;
    }""",
            """    public static long getOnlyProfileEmojiId(TLRPC.User user) {
        if (TeleBetaLocalProfileStyle.getProfileCollectible(UserConfig.selectedAccount, user) != null) {
            return 0L;
        }
        long fallback = user != null && user.profile_color instanceof TLRPC.TL_peerColor && (user.profile_color.flags & 2) != 0
            ? user.profile_color.background_emoji_id : 0L;
        return TeleBetaLocalProfileStyle.getProfileEmoji(UserConfig.selectedAccount, user, fallback);
    }""",
            "UserObject.getOnlyProfileEmojiId",
        ),
        (
            """    public static long getProfileCollectibleId(TLRPC.User user) {
        if (user != null && user.emoji_status instanceof TLRPC.TL_emojiStatusCollectible) {
            return ((TLRPC.TL_emojiStatusCollectible) user.emoji_status).collectible_id;
        }
        return 0;
    }""",
            """    public static long getProfileCollectibleId(TLRPC.User user) {
        long fallback = user != null && user.emoji_status instanceof TLRPC.TL_emojiStatusCollectible
            ? ((TLRPC.TL_emojiStatusCollectible) user.emoji_status).collectible_id : 0L;
        return TeleBetaLocalProfileStyle.getProfileCollectibleId(UserConfig.selectedAccount, user, fallback);
    }""",
            "UserObject.getProfileCollectibleId",
        ),
    )
    for old, new, label in replacements:
        source = _replace_exact(source, old, new, 1, label)
    return source


TARGETS = ("messenger/UserObject.java",)


def patch_peer_color_activity(source: str) -> str:
    source = _ensure_import(
        source,
        "import org.telegram.messenger.UserConfig;\\n",
        "import org.telegram.messenger.TeleBetaFreemium;\\nimport org.telegram.messenger.TeleBetaLocalProfileStyle;\\n",
        "PeerColorActivity",
    )
    source = _replace_exact(
        source,
        "getUserConfig().isPremium()",
        "(getUserConfig().isPremium() || TeleBetaFreemium.isActive(currentAccount))",
        5,
        "PeerColorActivity account-local entitlement checks",
    )
    source = _replace_exact(
        source,
        """                    selectedEmojiCollectible = user != null && user.emoji_status instanceof TLRPC.TL_emojiStatusCollectible ? (TLRPC.TL_emojiStatusCollectible) user.emoji_status : null;
                    selectedPeerCollectible = null;""",
        """                    TLRPC.TL_emojiStatusCollectible localProfileCollectible = TeleBetaLocalProfileStyle.getProfileCollectible(currentAccount, user);
                    selectedEmojiCollectible = localProfileCollectible != null ? localProfileCollectible : (user != null && user.emoji_status instanceof TLRPC.TL_emojiStatusCollectible ? (TLRPC.TL_emojiStatusCollectible) user.emoji_status : null);
                    selectedPeerCollectible = null;""",
        1,
        "PeerColorActivity restore local profile collectible",
    )
    source = _replace_exact(
        source,
        """                    selectedEmojiCollectible = null;
                    selectedPeerCollectible = user != null && user.color instanceof TLRPC.TL_peerColorCollectible ? (TLRPC.TL_peerColorCollectible) user.color : null;""",
        """                    selectedEmojiCollectible = null;
                    TLRPC.TL_peerColorCollectible localNameCollectible = TeleBetaLocalProfileStyle.getNameCollectible(currentAccount, user);
                    selectedPeerCollectible = localNameCollectible != null ? localNameCollectible : (user != null && user.color instanceof TLRPC.TL_peerColorCollectible ? (TLRPC.TL_peerColorCollectible) user.color : null);""",
        1,
        "PeerColorActivity restore local name collectible",
    )
    source = _replace_exact(
        source,
        """    private void buttonClick() {
        if (loading) {
            return;
        }
        if (isChannel) {""",
        """    private void buttonClick() {
        if (loading) {
            return;
        }
        if (isTeleBetaLocalProfileStyleEnabled()) {
            apply();
            finishFragment();
            showBulletin();
            return;
        }
        if (isChannel) {""",
        1,
        "PeerColorActivity local button flow",
    )
    source = _replace_exact(
        source,
        """        public void updateButton(boolean animated) {
            if (selectedResaleGift != null) {""",
        """        public void updateButton(boolean animated) {
            if (selectedResaleGift != null && !isTeleBetaLocalProfileStyleEnabled()) {""",
        1,
        "PeerColorActivity local resale-button handling",
    )
    source = _replace_exact(
        source,
        "    private boolean applyingName, applyingProfile;",
        """    private boolean isTeleBetaLocalProfileStyleEnabled() {
        return !isChannel && (UserConfig.getInstance(currentAccount).isPremium() || TeleBetaFreemium.isActive(currentAccount));
    }

    private boolean applyingName, applyingProfile;""",
        1,
        "PeerColorActivity local entitlement helper",
    )
    source = _replace_exact(
        source,
        """            final TLRPC.User me = getUserConfig().getCurrentUser();
            if (me.color == null) {""",
        """            final TLRPC.User me = getUserConfig().getCurrentUser();
            if (isTeleBetaLocalProfileStyleEnabled()) {
                TeleBetaLocalProfileStyle.save(
                    currentAccount,
                    me.id,
                    namePage.selectedColor,
                    profilePage.selectedColor,
                    profilePage.selectedEmoji,
                    namePage.selectedPeerCollectible,
                    profilePage.selectedEmojiCollectible
                );
                NotificationCenter.getInstance(currentAccount).postNotificationName(
                    NotificationCenter.updateInterfaces,
                    MessagesController.UPDATE_MASK_NAME | MessagesController.UPDATE_MASK_AVATAR
                );
                return;
            }
            if (me.color == null) {""",
        1,
        "PeerColorActivity local profile style persistence",
    )
    source = _replace_exact(
        source,
        "                } else if (selectedColor < 7) {",
        "                } else if (selectedColor >= 0 && selectedColor < Theme.keys_avatar_nameInMessage.length) {",
        1,
        "PeerColorActivity selected-color palette bounds",
    )
    source = _replace_exact(
        source,
        "if (colorId < 7)",
        "if (colorId >= 0 && colorId < Theme.keys_avatar_nameInMessage.length)",
        3,
        "PeerColorActivity color-id palette bounds",
    )
    source = _replace_exact(
        source,
        """                final ArrayList<Integer> colors = dark && p.dark_colors != null ? p.dark_colors : p.colors;

                final int color1 = colors.get(0) | 0xFF000000;""",
        """                ArrayList<Integer> colors = dark && p.dark_colors != null && !p.dark_colors.isEmpty() ? p.dark_colors : p.colors;
                if (colors == null || colors.isEmpty()) {
                    colors = new ArrayList<>();
                    colors.add(p.accent_color);
                }

                final int color1 = colors.get(0) | 0xFF000000;""",
        2,
        "PeerColorActivity collectible palette fallback",
    )
    return source


def patch_profile_activity(source: str) -> str:
    source = _ensure_import(
        source,
        "import org.telegram.messenger.UserObject;\\n",
        "import org.telegram.messenger.TeleBetaFreemium;\\nimport org.telegram.messenger.TeleBetaLocalProfileStyle;\\n",
        "ProfileActivity",
    )
    source = _replace_exact(
        source,
        "getUserConfig().isPremium()",
        "(getUserConfig().isPremium() || TeleBetaFreemium.isActive(currentAccount))",
        5,
        "ProfileActivity account-local entitlement checks",
    )
    source = _replace_exact(
        source,
        "UserConfig.getInstance(currentAccount).isPremium()",
        "(UserConfig.getInstance(currentAccount).isPremium() || TeleBetaFreemium.isActive(currentAccount))",
        3,
        "ProfileActivity account-local entitlement checks",
    )
    return _replace_exact(
        source,
        "            peerColor = MessagesController.PeerColor.fromCollectible(user.emoji_status);",
        """            TLRPC.TL_emojiStatusCollectible localProfileCollectible = TeleBetaLocalProfileStyle.getProfileCollectible(currentAccount, user);
            if (localProfileCollectible != null) {
                user.emoji_status = localProfileCollectible;
            }
            peerColor = MessagesController.PeerColor.fromCollectible(user.emoji_status);""",
        1,
        "ProfileActivity local collectible rendering",
    )


TARGETS = (
    "messenger/UserObject.java",
    "ui/PeerColorActivity.java",
    "ui/ProfileActivity.java",
)
