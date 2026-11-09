"""Local Download Manager patch for Tele-beta.

Adds a device-local task queue around Telegram FileLoader. It does not change
Telegram account entitlements, server byte budgets, or network throughput.
"""
from pathlib import Path
import re

ROOT = Path(".")


def _replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return source.replace(old, new, 1)


def apply_local_download_manager() -> None:
    engine = ROOT / "TMessagesProj/src/main/java/org/telegram/messenger/TeleBetaFreemium.java"
    if not engine.exists():
        raise SystemExit("TeleBetaFreemium.java missing; apply_freemium() must run first.")
    engine_source = engine.read_text(encoding="utf-8")
    enum_match = re.search(r"public\s+enum\s+Feature\s*\{([^}]*)\}", engine_source)
    if enum_match is None:
        raise SystemExit("Could not locate the Freemium Feature enum.")
    feature_names = [name.strip() for name in enum_match.group(1).split(",") if name.strip()]
    if "LOCAL_DOWNLOAD_MANAGER" not in feature_names:
        feature_names.append("LOCAL_DOWNLOAD_MANAGER")
        replacement = "public enum Feature { " + ", ".join(feature_names) + " }"
        engine_source = engine_source[:enum_match.start()] + replacement + engine_source[enum_match.end():]
        engine.write_text(engine_source, encoding="utf-8")

    helper = ROOT / "TMessagesProj/src/main/java/org/telegram/messenger/TeleBetaLocalDownloadManager.java"
    if helper.exists():
        raise SystemExit(f"Refusing to overwrite existing source file: {helper}")

    helper_source = r"""package org.telegram.messenger;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.os.Handler;
import android.os.Looper;
import android.text.TextUtils;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import org.telegram.tgnet.TLRPC;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.ActionBar.Theme;

import java.io.File;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * Local task policy and queue for downloads initiated through Telegram's
 * existing FileLoader. It never changes server-side limits or byte budgets.
 *
 * Current safe scope: document messages only. Photos, streaming media,
 * secret media and automatically initiated downloads stay on upstream paths.
 */
public final class TeleBetaLocalDownloadManager {
    public static final int STATUS_QUEUED = 0;
    public static final int STATUS_DOWNLOADING = 1;
    public static final int STATUS_PAUSED = 2;
    public static final int STATUS_COMPLETED = 3;
    public static final int STATUS_FAILED = 4;
    public static final int STATUS_CANCELLED = 5;

    private static final String PREFS = "telebeta_local_download_manager";
    private static final String KEY_TASKS = "tasks";
    private static final String KEY_WIFI_ONLY = "wifi_only";
    private static final String KEY_MAX_PARALLEL = "max_parallel";
    private static final String KEY_SAVE_TREE = "save_tree";
    public static final int REQUEST_ADD_DOWNLOAD = 987656;
    private static final int MAX_TASKS = 500;

    private static final Handler MAIN = new Handler(Looper.getMainLooper());
    private static volatile TeleBetaLocalDownloadManager[] instances =
            new TeleBetaLocalDownloadManager[UserConfig.MAX_ACCOUNT_COUNT];

    public static final class Task {
        public String fileName;
        public long documentId;
        public long accessHash;
        public int dcId;
        public String fileReference;
        public String mimeType;
        public String displayName;
        public long size;
        public long scheduleAt;
        public int priority;
        public int status;
        public int account;
        public long createdAt;

        JSONObject toJson() throws JSONException {
            JSONObject o = new JSONObject();
            o.put("fileName", fileName);
            o.put("documentId", documentId);
            o.put("accessHash", accessHash);
            o.put("dcId", dcId);
            o.put("fileReference", fileReference == null ? "" : fileReference);
            o.put("mimeType", mimeType == null ? "" : mimeType);
            o.put("displayName", displayName == null ? fileName : displayName);
            o.put("size", size);
            o.put("scheduleAt", scheduleAt);
            o.put("priority", priority);
            o.put("status", status);
            o.put("account", account);
            o.put("createdAt", createdAt);
            return o;
        }

        static Task fromJson(JSONObject o) {
            Task t = new Task();
            t.fileName = o.optString("fileName", "");
            t.documentId = o.optLong("documentId");
            t.accessHash = o.optLong("accessHash");
            t.dcId = o.optInt("dcId");
            t.fileReference = o.optString("fileReference", "");
            t.mimeType = o.optString("mimeType", "");
            t.displayName = o.optString("displayName", t.fileName);
            t.size = o.optLong("size");
            t.scheduleAt = o.optLong("scheduleAt");
            t.priority = o.optInt("priority");
            t.status = o.optInt("status", STATUS_QUEUED);
            t.account = o.optInt("account");
            t.createdAt = o.optLong("createdAt");
            return t;
        }

        TLRPC.TL_document toDocument() {
            TLRPC.TL_document d = new TLRPC.TL_document();
            d.id = documentId;
            d.access_hash = accessHash;
            d.dc_id = dcId;
            d.file_reference = decodeReference(fileReference);
            d.mime_type = mimeType;
            d.size = size;
            d.date = 0;
            d.attributes = new ArrayList<>();
            return d;
        }
    }

    private final int account;
    private static final TeleBetaLocalDownloadManager[] CALLBACKS = new TeleBetaLocalDownloadManager[UserConfig.MAX_ACCOUNT_COUNT];
    private final SharedPreferences prefs;
    private volatile boolean wifiOnlyOverride;

    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private final ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();
    private final List<Task> tasks = new ArrayList<>();
    private boolean workerRunning;
    private volatile long defaultScheduleDelayMinutes;
    private volatile java.util.WeakHashMap<String, MessageObject> parents = new java.util.WeakHashMap<>();

    public static TeleBetaLocalDownloadManager getInstance(int account) {
        TeleBetaLocalDownloadManager value = instances[account];
        if (value == null) {
            synchronized (TeleBetaLocalDownloadManager.class) {
                value = instances[account];
                if (value == null) {
                    instances[account] = value = new TeleBetaLocalDownloadManager(account);
                }
            }
        }
        return value;
    }

    private TeleBetaLocalDownloadManager(int account) {
        this.account = account;
        CALLBACKS[account] = this;
        prefs = ApplicationLoader.applicationContext.getSharedPreferences(PREFS + "_" + account, Context.MODE_PRIVATE);
        wifiOnlyOverride = prefs.getBoolean(KEY_WIFI_ONLY, false);
        defaultScheduleDelayMinutes = prefs.getLong("schedule_delay_minutes", 0);
        load();
        scheduler.scheduleWithFixedDelay(this::pump, 2, 2, TimeUnit.SECONDS);
    }

    private synchronized void load() {
        tasks.clear();
        try {
            JSONArray array = new JSONArray(prefs.getString(KEY_TASKS, "[]"));
            for (int i = 0; i < array.length() && i < MAX_TASKS; i++) {
                JSONObject item = array.optJSONObject(i);
                if (item == null) continue;
                Task task = Task.fromJson(item);
                if (task.fileName.isEmpty() || task.account != account) continue;
                if (task.status == STATUS_DOWNLOADING) task.status = STATUS_QUEUED;
                if (task.status != STATUS_COMPLETED && task.status != STATUS_CANCELLED) tasks.add(task);
            }
        } catch (JSONException ignored) {
            tasks.clear();
        }
        persist();
    }

    private synchronized void persist() {
        JSONArray array = new JSONArray();
        try {
            for (Task task : tasks) array.put(task.toJson());
        } catch (JSONException e) {
            FileLog.e(e);
        }
        prefs.edit().putString(KEY_TASKS, array.toString()).commit();
    }

    public synchronized List<Task> getTasks() {
        return new ArrayList<>(tasks);
    }

    public static void notifyCompleted(int account, String fileName) {
        TeleBetaLocalDownloadManager manager = account >= 0 && account < CALLBACKS.length ? CALLBACKS[account] : null;
        if (manager != null) manager.updateStatus(fileName, STATUS_COMPLETED);
    }

    public static void notifyFailed(int account, String fileName) {
        TeleBetaLocalDownloadManager manager = account >= 0 && account < CALLBACKS.length ? CALLBACKS[account] : null;
        if (manager != null) manager.updateStatus(fileName, STATUS_FAILED);
    }

    private synchronized void updateStatus(String fileName, int status) {
        Task task = find(fileName);
        if (task == null || task.status == STATUS_CANCELLED) return;
        task.status = status;
        if (status == STATUS_COMPLETED || status == STATUS_FAILED) parents.remove(fileName);
        persist();
        notifyQueueChanged(account);
        pump();
    }

    public synchronized boolean enqueue(TLRPC.Document document, String displayName, long scheduleAt, int priority) {
        return enqueue(document, displayName, scheduleAt, priority, null);
    }

    public synchronized boolean enqueue(TLRPC.Document document, String displayName, long scheduleAt, int priority, MessageObject parent) {
        if (document == null || document.id == 0 || document.dc_id == 0 || document.key != null) return false;
        String fileName = FileLoader.getAttachFileName(document);
        for (Task existing : tasks) {
            if (existing.fileName.equals(fileName) && existing.status != STATUS_CANCELLED && existing.status != STATUS_FAILED) {
                return true;
            }
        }
        if (tasks.size() >= MAX_TASKS) return false;
        Task task = new Task();
        task.fileName = fileName;
        task.documentId = document.id;
        task.accessHash = document.access_hash;
        task.dcId = document.dc_id;
        task.fileReference = encodeReference(document.file_reference);
        task.mimeType = document.mime_type;
        task.displayName = TextUtils.isEmpty(displayName) ? FileLoader.getDocumentFileName(document) : displayName;
        task.size = document.size;
        task.scheduleAt = Math.max(0, scheduleAt > 0 ? scheduleAt : (defaultScheduleDelayMinutes > 0 ? System.currentTimeMillis() + TimeUnit.MINUTES.toMillis(defaultScheduleDelayMinutes) : 0));
        task.priority = priority;
        task.status = STATUS_QUEUED;
        task.account = account;
        task.createdAt = System.currentTimeMillis();
        tasks.add(task);
        if (parent != null) parents.put(fileName, parent);
        persist();
        notifyQueueChanged(account);
        pump();
        return true;
    }

    public synchronized void pause(String fileName) {
        Task task = find(fileName);
        if (task == null || task.status == STATUS_COMPLETED) return;
        if (task.status == STATUS_QUEUED) {
            task.status = STATUS_PAUSED;
            persist();
            notifyQueueChanged(account);
            return;
        }
        task.status = STATUS_PAUSED;
        persist();
        notifyQueueChanged(account);
        FileLoadOperation operation = FileLoader.getInstance(account).getLoadOperation(fileName);
        if (operation != null) {
            FileLoader.getInstance(account).getFileLoaderQueue().postRunnable(() -> {
                operation.pause();
                MAIN.post(() -> {
                    synchronized (TeleBetaLocalDownloadManager.this) {
                        Task current = find(fileName);
                        if (current != null && current.status == STATUS_PAUSED) persist();
                    }
                    pump();
                });
            });
        }
    }

    public synchronized void resume(String fileName) {
        Task task = find(fileName);
        if (task == null || task.status == STATUS_COMPLETED) return;
        task.status = STATUS_QUEUED;
        persist();
        notifyQueueChanged(account);
        pump();
    }

    public synchronized void cancel(String fileName) {
        Task task = find(fileName);
        if (task == null) return;
        task.status = STATUS_CANCELLED;
        persist();
        notifyQueueChanged(account);
        FileLoader.getInstance(account).cancelLoadFile(fileName);
        pump();
    }

    public synchronized void setPriority(String fileName, int priority) {
        Task task = find(fileName);
        if (task == null) return;
        task.priority = Math.max(0, Math.min(3, priority));
        persist();
        notifyQueueChanged(account);
        FileLoader.getInstance(account).changePriority(priorityToLoader(task.priority), task.toDocument(), null, null, null, null, null);
    }

    public synchronized void setSchedule(String fileName, long timestamp) {
        Task task = find(fileName);
        if (task == null) return;
        task.scheduleAt = Math.max(0, timestamp);
        task.status = STATUS_QUEUED;
        persist();
        notifyQueueChanged(account);
        pump();
    }

    public void setWifiOnly(boolean enabled) {
        wifiOnlyOverride = enabled;
        prefs.edit().putBoolean(KEY_WIFI_ONLY, enabled).commit();
        pump();
    }

    public boolean isWifiOnly() {
        return prefs.getBoolean(KEY_WIFI_ONLY, false);
    }

    public void setMaxParallel(int count) {
        prefs.edit().putInt(KEY_MAX_PARALLEL, Math.max(1, Math.min(4, count))).commit();
        pump();
    }

    public int getMaxParallel() {
        return prefs.getInt(KEY_MAX_PARALLEL, 2);
    }

    public void setDefaultScheduleDelayMinutes(long minutes) {
        defaultScheduleDelayMinutes = Math.max(0, Math.min(minutes, 60L * 24L * 30L));
        prefs.edit().putLong("schedule_delay_minutes", defaultScheduleDelayMinutes).commit();
    }

    public long getDefaultScheduleDelayMinutes() {
        return defaultScheduleDelayMinutes;
    }

    public void setSaveTreeUri(String uri) {
        prefs.edit().putString(KEY_SAVE_TREE, uri == null ? "" : uri).commit();
    }

    public String getSaveTreeUri() {
        return prefs.getString(KEY_SAVE_TREE, "");
    }

    /** Add local tasks to Telegram's native Downloads row lists. */
    public synchronized void appendTelegramDownloadLists(ArrayList<MessageObject> active, ArrayList<MessageObject> recent) {
        if (!TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.LOCAL_DOWNLOAD_MANAGER)) return;
        for (Task task : tasks) {
            if (task.status == STATUS_CANCELLED || task.status == STATUS_FAILED || task.status == STATUS_COMPLETED) continue;
            TLRPC.TL_message message = new TLRPC.TL_message();
            message.id = (int) -Math.max(1L, task.createdAt);
            message.date = (int) (task.createdAt / 1000L);
            message.peer_id = new TLRPC.TL_peerUser();
            message.peer_id.user_id = UserConfig.getInstance(account).getClientUserId();
            message.from_id = new TLRPC.TL_peerUser();
            message.from_id.user_id = UserConfig.getInstance(account).getClientUserId();
            message.media = new TLRPC.TL_messageMediaDocument();
            message.media.document = task.toDocument();
            MessageObject row = new MessageObject(account, message, false, false);
            row.isDownloadingFile = true;
            if (task.status == STATUS_DOWNLOADING) active.add(0, row); else recent.add(0, row);
        }
    }

    public static void notifyQueueChanged(int account) {
        if (account < 0 || account >= CALLBACKS.length) return;
        TeleBetaLocalDownloadManager manager = CALLBACKS[account];
        if (manager != null) {
            MAIN.post(() -> NotificationCenter.getInstance(account).postNotificationName(NotificationCenter.onDownloadingFilesChanged));
        }
    }

    public synchronized void appendTelegramDownloadLists(ArrayList<MessageObject> active, ArrayList<MessageObject> recent) {
        if (!TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.LOCAL_DOWNLOAD_MANAGER)) return;
        for (Task task : tasks) {
            if (task.status == STATUS_CANCELLED || task.status == STATUS_FAILED || task.status == STATUS_COMPLETED) continue;
            MessageObject row = createTelegramDownloadsRow(task);
            if (task.status == STATUS_DOWNLOADING) active.add(0, row); else recent.add(0, row);
        }
    }

    private synchronized Task find(String fileName) {
        for (Task task : tasks) if (task.fileName.equals(fileName)) return task;
        return null;
    }

    private MessageObject createTelegramDownloadsRow(Task task) {
        TLRPC.TL_message message = new TLRPC.TL_message();
        message.id = (int) -Math.max(1L, task.createdAt);
        message.date = (int) (task.createdAt / 1000L);
        message.peer_id = new TLRPC.TL_peerUser();
        message.peer_id.user_id = UserConfig.getInstance(account).getClientUserId();
        message.from_id = new TLRPC.TL_peerUser();
        message.from_id.user_id = UserConfig.getInstance(account).getClientUserId();
        message.media = new TLRPC.TL_messageMediaDocument();
        message.media.document = task.toDocument();
        MessageObject row = new MessageObject(account, message, false, false);
        row.isDownloadingFile = true;
        return row;
    }

    private void pump() {
        synchronized (this) {
            if (workerRunning) return;
            workerRunning = true;
        }
        worker.execute(() -> {
            try {
                while (true) {
                    Task next;
                    synchronized (this) {
                        int active = 0;
                        for (Task task : tasks) {
                            if (task.status == STATUS_DOWNLOADING) active++;
                        }
                        if (isWifiOnly() && !isWifiConnected()) {
                            for (Task task : tasks) {
                                if (task.status != STATUS_DOWNLOADING) continue;
                                FileLoadOperation operation = FileLoader.getInstance(account).getLoadOperation(task.fileName);
                                if (operation != null && !operation.isPaused()) {
                                    FileLoader.getInstance(account).getFileLoaderQueue().postRunnable(operation::pause);
                                }
                                task.status = STATUS_QUEUED;
                            }
                            persist();
                            break;
                        }
                        if (active >= getMaxParallel()) break;
                        next = null;
                        long now = System.currentTimeMillis();
                        for (Task task : tasks) {
                            if (task.status != STATUS_QUEUED || task.scheduleAt > now) continue;
                            if (next == null || task.priority > next.priority ||
                                    task.priority == next.priority && task.createdAt < next.createdAt) next = task;
                        }
                        if (next == null) break;
                        next.status = STATUS_DOWNLOADING;
                        persist();
                    }
                    Task selected = next;
                    MAIN.post(() -> start(selected));
                    synchronized (this) { workerRunning = false; }
                    pump();
                    return;
                }
            } finally {
                synchronized (this) { workerRunning = false; }
            }
        });
    }

    private void start(Task task) {
        synchronized (this) {
            if (task.status != STATUS_DOWNLOADING) return;
            FileLoadOperation existing = FileLoader.getInstance(account).getLoadOperation(task.fileName);
            if (existing != null) {
                if (existing.isPaused()) FileLoader.getInstance(account).getFileLoaderQueue().postRunnable(existing::start);
                return;
            }
        }
        TLRPC.TL_message message = new TLRPC.TL_message();
        message.id = 0;
        message.date = (int) (System.currentTimeMillis() / 1000L);
        message.peer_id = new TLRPC.TL_peerUser();
        message.peer_id.user_id = UserConfig.getInstance(account).getClientUserId();
        message.from_id = new TLRPC.TL_peerUser();
        message.from_id.user_id = UserConfig.getInstance(account).getClientUserId();
        message.media = new TLRPC.TL_messageMediaDocument();
        message.media.document = task.toDocument();
        MessageObject parent = new MessageObject(account, message, false, false);
        MessageObject sourceParent;
        synchronized (this) { sourceParent = parents.get(task.fileName); }
        FileLoader.getInstance(account).loadFile(task.toDocument(), sourceParent != null ? sourceParent : parent, priorityToLoader(task.priority), 0);
        notifyQueueChanged(account);
    }

    private static int priorityToLoader(int priority) {
        switch (priority) {
            case 3: return FileLoader.PRIORITY_HIGH;
            case 2: return FileLoader.PRIORITY_NORMAL_UP;
            case 1: return FileLoader.PRIORITY_NORMAL;
            default: return FileLoader.PRIORITY_LOW;
        }
    }

    private boolean isWifiConnected() {
        try {
            ConnectivityManager cm = (ConnectivityManager) ApplicationLoader.applicationContext.getSystemService(Context.CONNECTIVITY_SERVICE);
            Network active = cm.getActiveNetwork();
            NetworkCapabilities caps = active == null ? null : cm.getNetworkCapabilities(active);
            return caps != null && caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI);
        } catch (Throwable ignored) {
            return false;
        }
    }

    private static String encodeReference(byte[] bytes) {
        if (bytes == null) return "";
        return android.util.Base64.encodeToString(bytes, android.util.Base64.NO_WRAP);
    }

    private static byte[] decodeReference(String value) {
        try { return TextUtils.isEmpty(value) ? new byte[0] : android.util.Base64.decode(value, android.util.Base64.DEFAULT); }
        catch (IllegalArgumentException ignored) { return new byte[0]; }
    }

    public static void showManager(BaseFragment fragment, int account, Theme.ResourcesProvider resourcesProvider) {
        if (fragment == null || fragment.getContext() == null) return;
        if (!TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.LOCAL_DOWNLOAD_MANAGER)) return;
        TeleBetaLocalDownloadManager manager = getInstance(account);
        List<Task> tasks = manager.getTasks();
        CharSequence[] labels = new CharSequence[tasks.size()];
        for (int i = 0; i < tasks.size(); i++) {
            Task task = tasks.get(i);
            String state = task.status == STATUS_PAUSED ? "Paused" :
                    task.status == STATUS_DOWNLOADING ? "Downloading" :
                    task.status == STATUS_COMPLETED ? "Completed" :
                    task.status == STATUS_FAILED ? "Failed" : "Queued";
            labels[i] = task.displayName + " — " + state;
        }
        AlertDialog.Builder builder = new AlertDialog.Builder(fragment.getContext(), resourcesProvider)
                .setTitle("Local Download Manager");
        if (labels.length == 0) {
            builder.setMessage("No managed downloads yet. Use a message menu and choose Add to Local Download Manager.");
        } else {
            builder.setItems(labels, (dialog, which) -> {
                if (which < 0 || which >= tasks.size()) return;
                Task task = tasks.get(which);
                if (task.status == STATUS_PAUSED) manager.resume(task.fileName);
                else if (task.status == STATUS_DOWNLOADING || task.status == STATUS_QUEUED) manager.pause(task.fileName);
            });
        }
        builder.setPositiveButton("Settings", (dialog, which) -> showSettings(fragment, manager, resourcesProvider));
        builder.setNegativeButton("Close", null);
        fragment.showDialog(builder.create());
    }

    public static void addFromMessage(BaseFragment fragment, MessageObject messageObject, int account, Theme.ResourcesProvider resourcesProvider) {
        if (fragment == null || messageObject == null || messageObject.getDocument() == null) return;
        if (!TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.LOCAL_DOWNLOAD_MANAGER)) return;
        TLRPC.Document document = messageObject.getDocument();
        TeleBetaLocalDownloadManager manager = getInstance(account);
        if (manager.enqueue(document, FileLoader.getDocumentFileName(document), 0, 1, messageObject)) {
            Toast.makeText(fragment.getContext(), "Added to Local Download Manager", Toast.LENGTH_SHORT).show();
        } else {
            Toast.makeText(fragment.getContext(), "This file cannot be managed", Toast.LENGTH_SHORT).show();
        }
    }

    private static void styleSettingsInput(EditText input, Theme.ResourcesProvider resourcesProvider) {
        input.setSingleLine(true);
        input.setTextColor(Theme.getColor(Theme.key_dialogTextBlack, resourcesProvider));
        input.setHintTextColor(Theme.getColor(Theme.key_dialogTextHint, resourcesProvider));
        input.setBackground(Theme.createEditTextDrawable(input.getContext(), true));
        input.setPadding(AndroidUtilities.dp(4), AndroidUtilities.dp(8),
                AndroidUtilities.dp(4), AndroidUtilities.dp(8));
        input.setTextSize(16);
    }

    private static void addSettingsField(LinearLayout layout, Context context, String label,
            EditText input, Theme.ResourcesProvider resourcesProvider) {
        TextView title = new TextView(context);
        title.setText(label);
        title.setTextSize(13);
        title.setTextColor(Theme.getColor(Theme.key_dialogTextGray2, resourcesProvider));
        layout.addView(title, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT));
        layout.addView(input, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT));
        LinearLayout.LayoutParams spacer = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, AndroidUtilities.dp(14));
        layout.addView(new android.view.View(context), spacer);
    }

    private static void showSettings(BaseFragment fragment, TeleBetaLocalDownloadManager manager, Theme.ResourcesProvider resourcesProvider) {
        Context context = fragment.getContext();
        EditText wifiOnly = new EditText(context);
        wifiOnly.setHint("true / false");
        wifiOnly.setText(String.valueOf(manager.isWifiOnly()));
        styleSettingsInput(wifiOnly, resourcesProvider);

        EditText parallel = new EditText(context);
        parallel.setHint("1–4");
        parallel.setText(String.valueOf(manager.getMaxParallel()));
        styleSettingsInput(parallel, resourcesProvider);

        EditText schedule = new EditText(context);
        schedule.setHint("0 = start immediately");
        schedule.setText(String.valueOf(manager.getDefaultScheduleDelayMinutes()));
        styleSettingsInput(schedule, resourcesProvider);

        LinearLayout layout = new LinearLayout(context);
        layout.setOrientation(LinearLayout.VERTICAL);
        int pad = AndroidUtilities.dp(20);
        layout.setPadding(pad, pad, pad, 0);
        addSettingsField(layout, context, "Wi-Fi only", wifiOnly, resourcesProvider);
        addSettingsField(layout, context, "Maximum parallel downloads", parallel, resourcesProvider);
        addSettingsField(layout, context, "Default schedule delay (minutes)", schedule, resourcesProvider);

        AlertDialog dialog = new AlertDialog.Builder(context, resourcesProvider)
                .setTitle("Download settings")
                .setView(layout)
                .setPositiveButton("Save", (d, w) -> {
                    manager.setWifiOnly(Boolean.parseBoolean(wifiOnly.getText().toString().trim()));
                    try {
                        int count = Integer.parseInt(parallel.getText().toString().trim());
                        manager.setMaxParallel(count);
                    } catch (NumberFormatException ignored) {}
                    try {
                        long delay = Math.max(0, Long.parseLong(schedule.getText().toString().trim()));
                        manager.setDefaultScheduleDelayMinutes(delay);
                    } catch (NumberFormatException ignored) {}
                })
                .setNegativeButton("Cancel", null)
                .create();
        fragment.showDialog(dialog);
    }
}
"""
    helper.parent.mkdir(parents=True, exist_ok=True)
    helper.write_text(helper_source, encoding="utf-8")

    loader = ROOT / "TMessagesProj/src/main/java/org/telegram/messenger/FileLoader.java"
    loader_source = loader.read_text(encoding="utf-8")
    lookup_anchor = "    public boolean isLoadingFile(final String fileName) {\n"
    lookup_add = """    public FileLoadOperation getLoadOperation(final String fileName) {
        return fileName == null ? null : loadOperationPaths.get(fileName);
    }

    public boolean isLoadingFile(final String fileName) {
"""
    if "getLoadOperation(final String fileName)" not in loader_source:
        loader_source = _replace_once(loader_source, lookup_anchor, lookup_add, "FileLoader operation lookup")
    elif loader_source.count("getLoadOperation(final String fileName)") != 1:
        raise SystemExit("FileLoader operation lookup is ambiguous.")

    finish_anchor = """            public void didFinishLoadingFile(FileLoadOperation operation, File finalFile) {
"""
    finish_add = finish_anchor + """                TeleBetaLocalDownloadManager.notifyCompleted(currentAccount, fileName);
"""
    loader_source = _replace_once(loader_source, finish_anchor, finish_add, "FileLoader managed completion callback")
    failure_anchor = """            public void didFailedLoadingFile(FileLoadOperation operation, int reason) {
"""
    failure_add = failure_anchor + """                TeleBetaLocalDownloadManager.notifyFailed(currentAccount, fileName);
"""
    loader_source = _replace_once(loader_source, failure_anchor, failure_add, "FileLoader managed failure callback")
    loader.write_text(loader_source, encoding="utf-8")

    chat = ROOT / "TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java"
    chat_source = chat.read_text(encoding="utf-8")
    import_anchor = "import org.telegram.messenger.MessagesController;\n"
    import_line = "import org.telegram.messenger.TeleBetaLocalDownloadManager;\n"
    if import_line not in chat_source:
        chat_source = _replace_once(chat_source, import_anchor, import_anchor + import_line, "ChatActivity download manager import")
    menu_anchor = """        if (chatMode == MODE_QUICK_REPLIES && !QuickRepliesController.isSpecial(quickReplyShortcut)) {
            menu.addItem(edit_quick_reply, R.drawable.group_edit).setContentDescription(LocaleController.getString(R.string.Edit));
        }
"""
    menu_new = menu_anchor + """
        if (chatMode == MODE_DEFAULT && currentEncryptedChat == null && !isReport()
                && TeleBetaFreemium.getInstance().isFeatureEnabled(TeleBetaFreemium.Feature.LOCAL_DOWNLOAD_MANAGER)) {
            menu.addItem(987655, R.drawable.msg_download).setContentDescription("Local Download Manager");
        }
"""
    chat_source = _replace_once(chat_source, menu_anchor, menu_new, "ChatActivity download manager menu")
    click_anchor = """                } else if (id == edit_quick_reply) {
"""
    click_new = """                } else if (id == 987655) {
                    TeleBetaLocalDownloadManager.showManager(ChatActivity.this, currentAccount, getResourceProvider());
                } else if (id == edit_quick_reply) {
"""
    chat_source = _replace_once(chat_source, click_anchor, click_new, "ChatActivity download manager click")
    chat.write_text(chat_source, encoding="utf-8")

    # Keep the Freemium feature registry aligned with this manager.
    freemium_patch = ROOT / "patches/freemium/patch.py"
    freemium_source = freemium_patch.read_text(encoding="utf-8")
    old_feature = "public enum Feature { CUSTOM_THEMES, CHAT_CUSTOMIZATION, CUSTOM_UI, ADVANCED_DOWNLOADS, ADVANCED_PRIVACY, APP_ICONS }"
    new_feature = "public enum Feature { CUSTOM_THEMES, CHAT_CUSTOMIZATION, CUSTOM_UI, ADVANCED_DOWNLOADS, ADVANCED_PRIVACY, APP_ICONS, LOCAL_DOWNLOAD_MANAGER }"
    if new_feature not in freemium_source:
        if old_feature not in freemium_source:
            raise SystemExit("Freemium feature enum anchor changed; refusing unsafe edit.")
        freemium_source = freemium_source.replace(old_feature, new_feature, 1)
        freemium_patch.write_text(freemium_source, encoding="utf-8")
    if "LOCAL_DOWNLOAD_MANAGER" not in engine.read_text(encoding="utf-8"):
        raise SystemExit("Feature registry validation failed.")
