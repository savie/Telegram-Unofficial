"""Standalone patch for Tele-ß Local Quick Replies.

Creates on-device reply templates and inserts their text into the chat composer.
Does not use Telegram Business Quick Replies RPC.
"""
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT = REPO_ROOT / "upstream"


def _replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return source.replace(old, new, 1)


def apply_local_quick_replies() -> None:
    engine = ROOT / "TMessagesProj/src/main/java/org/telegram/messenger/TeleBetaFreemium.java"
    if not engine.exists():
        raise SystemExit("TeleBetaFreemium.java missing; apply_freemium() must run first.")
    engine_source = engine.read_text(encoding="utf-8")
    enum_match = re.search(r"public\s+enum\s+Feature\s*\{([^}]*)\}", engine_source)
    if enum_match is None:
        raise SystemExit("Could not locate the Freemium Feature enum.")
    feature_names = [name.strip() for name in enum_match.group(1).split(",") if name.strip()]
    if "LOCAL_QUICK_REPLIES" not in feature_names:
        feature_names.append("LOCAL_QUICK_REPLIES")
        replacement = "public enum Feature { " + ", ".join(feature_names) + " }"
        engine_source = engine_source[:enum_match.start()] + replacement + engine_source[enum_match.end():]
        engine.write_text(engine_source, encoding="utf-8")

    helper = ROOT / "TMessagesProj/src/main/java/org/telegram/messenger/TeleBetaLocalQuickReplies.java"
    if helper.exists():
        raise SystemExit(f"Refusing to overwrite existing source file: {helper}")

    helper_source = r"""package org.telegram.messenger;

import android.content.Context;
import android.content.SharedPreferences;
import android.text.InputType;
import android.text.TextUtils;
import android.view.Gravity;
import android.widget.EditText;
import android.widget.LinearLayout;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.ChatActivityEnterView;

public final class TeleBetaLocalQuickReplies {
    private static final String PREFS = "telebeta_local_quick_replies";
    private static final String KEY_ITEMS = "items";

    private TeleBetaLocalQuickReplies() {}

    private static SharedPreferences preferences(int account) {
        return ApplicationLoader.applicationContext.getSharedPreferences(PREFS + "_" + account, Context.MODE_PRIVATE);
    }

    private static JSONArray readItems(int account) {
        String raw = preferences(account).getString(KEY_ITEMS, "[]");
        try {
            JSONArray parsed = new JSONArray(raw);
            JSONArray valid = new JSONArray();
            for (int i = 0; i < parsed.length(); i++) {
                JSONObject item = parsed.optJSONObject(i);
                if (item == null) continue;
                String title = item.optString("title", "").trim();
                String body = item.optString("body", "");
                if (!title.isEmpty() && !body.trim().isEmpty()) {
                    JSONObject normalized = new JSONObject();
                    normalized.put("title", title);
                    normalized.put("body", body);
                    valid.put(normalized);
                }
            }
            return valid;
        } catch (JSONException ignored) {
            return new JSONArray();
        }
    }

    private static void writeItems(int account, JSONArray items) {
        preferences(account).edit().putString(KEY_ITEMS, items.toString()).commit();
    }

    private static String titleAt(JSONArray items, int index) {
        JSONObject item = items.optJSONObject(index);
        return item == null ? "" : item.optString("title", "");
    }

    private static String bodyAt(JSONArray items, int index) {
        JSONObject item = items.optJSONObject(index);
        return item == null ? "" : item.optString("body", "");
    }

    public static void showPicker(BaseFragment fragment, int account, ChatActivityEnterView composer, Theme.ResourcesProvider resourcesProvider) {
        if (fragment == null || fragment.getContext() == null || composer == null) return;
        if (!TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.LOCAL_QUICK_REPLIES)) return;
        Context context = fragment.getContext();
        JSONArray items = readItems(account);
        CharSequence[] labels = new CharSequence[items.length()];
        for (int i = 0; i < items.length(); i++) {
            String title = titleAt(items, i);
            String preview = bodyAt(items, i).replace('\n', ' ');
            if (preview.length() > 72) preview = preview.substring(0, 69) + "…";
            labels[i] = title + "\n" + preview;
        }
        AlertDialog.Builder builder = new AlertDialog.Builder(context, resourcesProvider)
            .setTitle("Local Quick Replies");
        if (labels.length == 0) {
            builder.setMessage("No quick replies yet.");
        } else {
            builder.setItems(labels, (dialog, which) -> {
                if (which < 0 || which >= items.length()) return;
                String body = bodyAt(items, which);
                CharSequence current = composer.getFieldText();
                String combined = TextUtils.isEmpty(current) ? body : current + "\n" + body;
                composer.setFieldText(combined);
            });
        }
        builder .setPositiveButton("Add", (dialog, which) -> showEditor(fragment, account, resourcesProvider, -1));
        builder .setNegativeButton("Manage", (dialog, which) -> showManager(fragment, account, resourcesProvider));
        builder.setNeutralButton("Close", null);
        fragment.showDialog(builder.create());
    }

    private static void showManager(BaseFragment fragment, int account, Theme.ResourcesProvider resourcesProvider) {
        JSONArray items = readItems(account);
        if (items.length() == 0) {
            showEditor(fragment, account, resourcesProvider, -1);
            return;
        }
        CharSequence[] labels = new CharSequence[items.length()];
        for (int i = 0; i < items.length(); i++) labels[i] = titleAt(items, i);
        AlertDialog dialog = new AlertDialog.Builder(fragment.getContext(), resourcesProvider)
            .setTitle("Manage Quick Replies")
            .setItems(labels, (d, which) -> showEditor(fragment, account, resourcesProvider, which))
            .setPositiveButton("Add", (d, which) -> showEditor(fragment, account, resourcesProvider, -1))
            .setNegativeButton("Close", null)
            .create();
        fragment.showDialog(dialog);
    }

    private static void showEditor(BaseFragment fragment, int account, Theme.ResourcesProvider resourcesProvider, int editIndex) {
        Context context = fragment.getContext();
        JSONArray items = readItems(account);
        boolean editing = editIndex >= 0 && editIndex < items.length();
        EditText title = new EditText(context);
        title.setSingleLine(true);
        title.setTextColor(Theme.getColor(Theme.key_dialogTextBlack, resourcesProvider));
        title.setHintTextColor(Theme.getColor(Theme.key_dialogTextHint, resourcesProvider));
        title.setHint("Shortcut name");
        title.setText(editing ? titleAt(items, editIndex) : "");
        title.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);

        EditText body = new EditText(context);
        body.setHint("Reply message");
        body.setTextColor(Theme.getColor(Theme.key_dialogTextBlack, resourcesProvider));
        body.setHintTextColor(Theme.getColor(Theme.key_dialogTextHint, resourcesProvider));
        body.setGravity(Gravity.TOP | Gravity.START);
        body.setMinLines(4);
        body.setMaxLines(10);
        body.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_MULTI_LINE | InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);
        body.setText(editing ? bodyAt(items, editIndex) : "");

        LinearLayout form = new LinearLayout(context);
        form.setOrientation(LinearLayout.VERTICAL);
        int padding = AndroidUtilities.dp(20);
        form.setPadding(padding, AndroidUtilities.dp(8), padding, 0);
        form.addView(title, new LinearLayout.LayoutParams(-1, AndroidUtilities.dp(48)));
        form.addView(body, new LinearLayout.LayoutParams(-1, AndroidUtilities.dp(140)));

        AlertDialog.Builder builder = new AlertDialog.Builder(context, resourcesProvider)
            .setTitle(editing ? "Edit Quick Reply" : "New Quick Reply")
            .setView(form)
            .setPositiveButton("Save", (dialog, which) -> {
                String name = title.getText().toString().trim();
                String text = body.getText().toString();
                if (name.isEmpty() || text.trim().isEmpty()) {
                    showEditor(fragment, account, resourcesProvider, editIndex);
                    return;
                }
                JSONArray current = readItems(account);
                JSONArray updated = new JSONArray();
                try {
                    JSONObject replacement = new JSONObject();
                    replacement.put("title", name);
                    replacement.put("body", text);
                    if (editing) {
                        for (int i = 0; i < current.length(); i++) {
                            updated.put(i == editIndex ? replacement : current.getJSONObject(i));
                        }
                    } else {
                        for (int i = 0; i < current.length(); i++) updated.put(current.getJSONObject(i));
                        updated.put(replacement);
                    }
                    writeItems(account, updated);
                } catch (JSONException ignored) {
                    FileLog.e("Unable to serialize local quick replies");
                }
            })
            .setNegativeButton("Cancel", null);
        if (editing) {
            builder.setNeutralButton("Delete", (dialog, which) -> {
                JSONArray current = readItems(account);
                JSONArray updated = new JSONArray();
                for (int i = 0; i < current.length(); i++) {
                    if (i != editIndex) updated.put(current.optJSONObject(i));
                }
                writeItems(account, updated);
            });
        }
        fragment.showDialog(builder.create());
    }
}
"""
    helper.parent.mkdir(parents=True, exist_ok=True)
    helper.write_text(helper_source, encoding="utf-8")

    chat = ROOT / "TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java"
    source = chat.read_text(encoding="utf-8")
    import_anchor = "import org.telegram.messenger.MessagesController;\n"
    import_lines = (
        "import org.telegram.messenger.TeleBetaFreemium;\n"
        "import org.telegram.messenger.TeleBetaLocalQuickReplies;\n"
    )
    if "import org.telegram.messenger.TeleBetaLocalQuickReplies;\n" not in source:
        source = _replace_once(source, import_anchor, import_anchor + import_lines, "ChatActivity imports")
    elif "import org.telegram.messenger.TeleBetaFreemium;\n" not in source:
        source = _replace_once(source, "import org.telegram.messenger.TeleBetaLocalQuickReplies;\n",
                               "import org.telegram.messenger.TeleBetaFreemium;\nimport org.telegram.messenger.TeleBetaLocalQuickReplies;\n",
                               "ChatActivity Freemium import")

    menu_anchor = """        if (chatMode == MODE_QUICK_REPLIES && !QuickRepliesController.isSpecial(quickReplyShortcut)) {
            menu.addItem(edit_quick_reply, R.drawable.group_edit).setContentDescription(LocaleController.getString(R.string.Edit));
        }
"""
    menu_new = menu_anchor + """
        if (chatMode == MODE_DEFAULT && currentEncryptedChat == null && !isReport()
                && TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.LOCAL_QUICK_REPLIES)) {
            menu.addItem(987654, R.drawable.msg_edit).setContentDescription("Local Quick Replies");
        }
"""
    source = _replace_once(source, menu_anchor, menu_new, "ChatActivity local quick replies menu")

    click_anchor = """                } else if (id == edit_quick_reply) {
"""
    click_new = """                } else if (id == 987654) {
                    TeleBetaLocalQuickReplies.showPicker(ChatActivity.this, currentAccount, chatActivityEnterView, getResourceProvider());
                } else if (id == edit_quick_reply) {
"""
    source = _replace_once(source, click_anchor, click_new, "ChatActivity local quick replies action")
    chat.write_text(source, encoding="utf-8")
