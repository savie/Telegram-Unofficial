# Audit Freemium Tele-ß

**Repositori:** `savie/Telegram-Unofficial`  
**Branch:** `master`  
**Commit yang diaudit:** `3373782567b90f94870eebb001f38f796cb6461e`  
**Upstream Telegram:** `3de37c8cfb039452be7398909461da6288babf15`  
**Tanggal:** 7 November 2026  
**Status:** Audit source; tidak ada implementasi atau perubahan source Telegram/modul pada pembaruan ini.

## 1. Batas audit

Audit difokuskan pada source Telegram Android yang telah di-vendor di root repository dan source modul yang dipakai build, terutama area Premium, Business, entitlement, dan request terkait.

Tidak termasuk:
- implementasi fitur baru;
- perubahan source Telegram atau source modul;
- perubahan workflow CI;
- perubahan status Premium akun Telegram di sisi client/server.

Tujuan produk: pengguna Tele-ß memperoleh paket Freemium lokal tanpa berlangganan Telegram Premium. Hak ini hanya berlaku untuk kemampuan yang dapat dijalankan dan diverifikasi di client. Fitur yang memerlukan entitlement atau validasi server Telegram tetap mengikuti aturan server.

## 2. Prinsip entitlement

Dua status wajib dipisahkan:

1. **Telegram Premium** — status akun yang diterima dari Telegram, direpresentasikan oleh `TLRPC.User.premium` dan `UserConfig.isPremium()`.
2. **Tele-ß Freemium** — entitlement produk lokal Tele-ß yang disimpan di perangkat.

Jangan mengubah `UserConfig.isPremium()`, memalsukan `TLRPC.User.premium`, atau menyuntikkan status Premium lokal ke request Telegram. Pemaksaan global akan membuka banyak call site yang tidak semuanya client-only, sementara server tetap dapat menolak operasinya.

## 3. Temuan engine dan jalur aktivasi Tele-ß saat ini

Pemeriksaan `patches/freemium/patch.py` menunjukkan build patch saat ini menghasilkan `TeleBetaFreemium.java` dan memodifikasi entry point di `PremiumPreviewFragment.java`.

Engine yang dihasilkan menyediakan:
- tier `FREE` dan `FREEMIUM`;
- feature key: `CUSTOM_THEMES`, `CHAT_CUSTOMIZATION`, `CUSTOM_UI`, `ADVANCED_DOWNLOADS`, `ADVANCED_PRIVACY`;
- penyimpanan `SharedPreferences` bernama `telebeta_freemium`;
- default tier `FREE` dan pemeriksaan feature default-deny;
- `grantFreemium()`, yang memberikan seluruh feature key lokal melalui `applyEntitlement(...)`;
- `isFreemiumActive()` untuk membaca tier yang tersimpan.

Patch juga mengganti implementasi `buyPremium(...)` menjadi grant lokal, mengganti teks CTA menjadi “Aktifkan Freemium”, dan mengatur `forcePremium` untuk menampilkan success presentation saat halaman dibuka kembali dengan source `freemium`.

**Penilaian:** jalur aktivasi lokal dan persistensi tier sudah tersedia pada patch build. Namun ini belum membuktikan fitur Premium upstream terbuka. Dari source yang ditelusuri, belum ditemukan integrasi feature key Tele-ß ke gate fitur upstream yang diaudit. Status visual sukses/CTA tidak sama dengan hak menjalankan fitur.

## 4. Temuan source Telegram dan modul

### 4.1 Identitas Premium dan propagasi ke native

- `UserConfig.isPremium()` mengembalikan `currentUser.premium`; bila user belum tersedia, hasilnya `false`.
- `ConnectionsManager.java` membaca `getCurrentUser().premium` ketika inisialisasi native.
- Nilai tersebut diteruskan melalui JNI `TgNetWrapper.cpp` ke `ConnectionsManager::init(..., userPremium, ...)`.
- `ConnectionsManager.cpp` menyimpan `currentUserPremium` dan menggunakannya pada pengaturan budget download serta perilaku request/flood-wait.

**Klasifikasi:** identitas Premium akun dan propagasi native bersifat account/server-linked. Jangan menggantinya dengan status Freemium Tele-ß.

### 4.2 Transkripsi suara

Pada `TranscribeButton.java`, request `TL_messages_transcribeAudio` tetap dikirim ke Telegram. Cabang non-Premium hanya menambahkan `RequestFlagDoNotWaitFloodWait`. Respons server membawa informasi trial/cooldown melalui `trial_remains_num` dan `trial_remains_until_date`.

**Klasifikasi:** server-dependent/hybrid. UI dan cara menangani flood-wait bukan bukti bahwa kuota transkripsi bisa dibuka dengan entitlement lokal.

### 4.3 Terjemahan

Pada `TranslateController.java`:
- `isFeatureAvailable()` mensyaratkan chat translation aktif dan `UserConfig.isPremium()`;
- overload per dialog juga mengizinkan `chat.autotranslation` sebagai kondisi khusus.

**Klasifikasi:** hybrid/server-controlled. Jangan mengganti syarat Premium akun secara massal. Perlu telusuri request dan konfigurasi per-dialog sebelum memutuskan apakah ada bagian UI lokal yang dapat diaktifkan.

### 4.4 Business / Quick Replies

Pada `QuickRepliesController.java`, pemanggilan `load()` tidak lagi berhenti berdasarkan status Premium (guard lama tampak dikomentari). Controller memuat data dari cache lokal `business_replies` dan melanjutkan proses pemuatan.

Pada `PremiumPreviewFragment.java`, klik item Business tetap memeriksa `getUserConfig().isPremium()` sebelum membuka halaman pengaturan seperti Location, Greeting Messages, Away Messages, Opening Hours, Chatbots, dan Quick Replies.

**Klasifikasi:** belum dapat dianggap client-only. Pengaturan Business dapat menyimpan atau menyinkronkan konfigurasi melalui API Telegram. Quick Replies memiliki penyimpanan cache lokal, tetapi itu tidak membuktikan operasi create/update/delete bebas dari server gate.

### 4.5 Rich Editor / Rich Messages

Pada `ChatAttachAlertRichLayout.java`:
- `sendSelectedItems()` memeriksa `MessagesController.richEditorAllowed()`;
- jika tidak diizinkan, konten non-lossy tertentu dikonversi menjadi pesan sederhana melalui composer;
- `showSendPreview()` masih memeriksa `UserConfig.isPremium()` dan menampilkan `PremiumFeatureBottomSheet`;
- tombol kirim dan toolbar juga mengunci bagian yang dianggap membutuhkan Premium.

Pada `RichEditor.java` dan `RichEditorToolbar.java`, status lock diteruskan ke tombol format tertentu. Pemeriksaan `richEditorAllowed()` dan `isPremium()` berperan bersama.

**Klasifikasi:** hybrid. Ada perilaku fallback client-side, tetapi kemampuan rich message, format payload, dan izin pengiriman perlu diuji terhadap server. Belum aman untuk membuka semua kontrol editor hanya dengan tier lokal.

### 4.6 Gift Premium

Pada `GiftPremiumBottomSheet.java`, callback sukses hadiah mengatur `user.premium = true`, menyimpan user melalui `MessagesController.putUser(...)`, dan mengirim notifikasi perubahan status.

**Klasifikasi:** jalur ini merupakan alur hadiah Telegram yang mengubah representasi status akun setelah transaksi/hadiah. Jangan gunakan callback ini sebagai grant Freemium Tele-ß dan jangan memanggilnya untuk aktivasi lokal.

### 4.7 Premium Preview dan katalog

`PremiumPreviewFragment.java` memuat katalog dan aksi untuk beragam fitur. Kartu katalog/preview bukan bukti implementasi fitur bisa dipakai tanpa Premium. Akses ke halaman Business pada source yang diperiksa masih memiliki pemeriksaan Premium akun.

### 4.8 Modul

Source modul yang dipakai build berada di bawah `TMessagesProj_Modules/`. Modul media yang diperiksa berisi konfigurasi Gradle untuk library media/ExoPlayer. Belum ada bukti dari pemeriksaan konfigurasi tersebut bahwa modul media menyediakan bypass entitlement Premium. Audit mendalam seluruh source modul—termasuk pemanggilan API lintas modul—masih diperlukan sebelum menyatakan inventaris modul selesai.

## 5. Matriks status awal

| Area | Bukti source | Klasifikasi | Keputusan audit |
|---|---|---|---|
| Status akun Premium | `UserConfig.isPremium()`, `TLRPC.User.premium` | Account/server-linked | Jangan disentuh |
| Native download budget | `ConnectionsManager.java`, JNI, `ConnectionsManager.cpp` | Account/server-linked | Jangan substitusi Freemium |
| Voice transcription | `TranscribeButton.java`, request Telegram dan trial fields | Server-dependent/hybrid | Tidak boleh bypass lokal |
| Chat translation | `TranslateController.java` | Hybrid/server-controlled | Telusuri API dan konfigurasi |
| Business settings | `PremiumPreviewFragment.java` | Hybrid/server-controlled | Perlu audit tiap operasi |
| Quick Replies | `QuickRepliesController.java` | Hybrid; cache lokal + sinkronisasi perlu ditelusuri | Belum boleh dibuka massal |
| Rich Editor | `ChatAttachAlertRichLayout.java`, `RichEditor.java` | Hybrid | Audit payload dan server validation |
| Premium gift | `GiftPremiumBottomSheet.java` | Transaksi/account entitlement | Pisahkan dari Freemium |
| Premium catalog | `PremiumPreviewFragment.java` | UI/upsell | Bukan gate fitur |

Tidak ada fitur pada matriks ini yang dinyatakan aman untuk dibuka hanya berdasarkan bukti yang tersedia saat audit ini.

## 6. Risiko dan ketidaksesuaian yang perlu ditindaklanjuti

1. **CTA sukses belum sama dengan feature access.** Aktivasi Freemium lokal sudah dapat tersimpan, tetapi source upstream yang diperiksa belum mengonsumsi feature key Tele-ß pada gate fitur.
2. **Feature key belum memetakan katalog.** Lima feature key saat ini belum memetakan seluruh katalog Premium maupun subfitur Business.
3. **Purchase entry point perlu inventaris penuh.** Penggantian `buyPremium(...)` pada satu entry point belum membuktikan semua CTA, deep link, bot, invoice, gift, dan jalur pembelian sudah dialihkan.
4. **Server gate tetap aktif.** Request transkripsi, terjemahan, Business, rich messages, dan operasi lain dapat tetap ditolak server walau UI lokal dibuka.
5. **Jangan gunakan callback hadiah.** `onGiftSuccess()` mengubah objek user menjadi Premium dan tidak sesuai untuk grant lokal.
6. **Modul belum diaudit penuh.** Perlu pencarian seluruh pemakaian `isPremium`, `premiumFeaturesBlocked`, `premiumPurchaseBlocked`, dan feature-specific gate pada source root serta semua source modul.

## 7. Rencana audit berikutnya — tanpa implementasi

1. Enumerasi semua call site `UserConfig.isPremium()` dan `TLRPC.User.premium` pada source root dan source modul.
2. Enumerasi `premiumFeaturesBlocked()`, `premiumPurchaseBlocked()`, limit Premium, feature-specific booleans, dan gate yang tidak memakai kata “premium”.
3. Untuk setiap gate, ikuti alur dari UI/caller sampai operasi akhir dan request Telegram.
4. Catat apakah data disimpan lokal, disinkronkan ke Telegram, atau divalidasi server.
5. Klasifikasikan tiap fitur sebagai **client-only**, **hybrid**, atau **server-dependent**, sertakan path dan bukti source.
6. Hanya setelah inventaris lengkap, pilih fitur client-only yang dapat menerima Tele-ß entitlement. Tidak ada perubahan source pada tahap audit.

## 8. Isolasi dokumentasi dari tiga workflow GitHub Actions

Folder `docs/` berada di luar path pemicu ketiga workflow saat ini. Hasil pemeriksaan konfigurasi:

| Workflow | Pemicu push saat ini | Dampak perubahan `docs/**` |
|---|---|---|
| `build-android.yml` | Daftar `paths` eksplisit untuk workflow itu, file pin upstream, Gradle, `TMessagesProj/**`, `TMessagesProj_AppStandalone/**`, dan `patches/**` | Tidak cocok dengan path filter; tidak memicu build |
| `migrate-telegram-vendored.yml` | Hanya `workflow_dispatch` | Tidak memiliki pemicu push; dokumen tidak memicu workflow |
| `sync-telegram-upstream.yml` | Daftar `paths` eksplisit hanya untuk workflow sync dan `UPSTREAM_TELEGRAM_COMMIT`, selain jadwal dan dispatch manual | Tidak cocok dengan path filter; tidak memicu sync |

Tidak perlu mengubah ketiga YAML untuk mengecualikan dokumentasi: filter push yang ada sudah tidak mencakup `docs/**`. Jangan menambahkan `docs/**` ke daftar `paths` workflow. Build workflow memang menyalin workspace ke direktori build sementara, tetapi penyalinan itu bukan pemicu workflow dan dokumentasi bukan input kompilasi.

Catatan: workflow `migrate-telegram-vendored.yml` tetap dapat dijalankan manual melalui `workflow_dispatch`; itu bukan akibat perubahan dokumen.

## 9. Catatan perubahan sesi ini

- Ditambahkan dokumen audit ke `docs/FREEMIUM_AUDIT.md`.
- Tidak mengubah source Telegram.
- Tidak mengubah source modul.
- Tidak mengubah tiga file workflow YAML.
- Tidak menjalankan CI atau build.
- Audit belum final; status fitur tetap mengikuti bukti source pada matriks di atas.

## 10. Audit lanjutan berdasarkan source `master`

**Baseline audit:** commit source `3373782567b90f94870eebb001f38f796cb6461e` (yang dipakai Build Android #96). Hasil pencarian GitHub dan pembacaan file penuh pada branch `master` setelah dokumentasi audit sebelumnya ditambahkan. Ini merupakan audit statis source; belum menggantikan pengujian runtime pada akun non-Premium.

### 10.1 Temuan penting: aktivasi lokal saat ini hanya mengganti tampilan, bukan entitlement fitur

Di `patches/freemium/patch.py`, `grantFreemium()` hanya menulis tier dan lima feature key ke SharedPreferences. Tetapi gate upstream yang diperiksa masih membaca `UserConfig.isPremium()`, `MessagesController.premiumFeaturesBlocked()`, limit konfigurasi Telegram, atau respons server. Belum ada pemakaian `TeleBetaFreemium.isFeatureEnabled(...)` yang menghubungkan entitlement lokal dengan fitur upstream pada source yang ditelusuri.

Ada masalah kedua pada alur sukses: method patch mengarahkan layar ke `PremiumPreviewFragment("freemium").setForcePremium()`. `forcePremium` adalah flag presentasi. Source constructor dan success UI memakainya untuk menampilkan tampilan subscribed, sementara status akun dan gate fitur tetap membaca status Premium yang sebenarnya. Jadi layar “You are all set” yang terlihat pada screenshot bukan bukti fitur telah diaktifkan.

**Kesimpulan valid dari source:** perilaku yang terlihat pada build #96 konsisten dengan aktivasi kosmetik/presentasi. Persistensi tier lokal bisa terjadi, tetapi belum mengubah otorisasi fitur Telegram di titik pemakaian. Patch satu method `buyPremium(...)` tidak cukup untuk menghasilkan akses Premium yang fungsional.

### 10.2 Business: sebagian besar operasi inti secara eksplisit memakai API Telegram

Source Business diperiksa sampai alur penyimpanan:

| Fitur | Source dan operasi | Hasil audit |
|---|---|---|
| Location | `Business/LocationActivity.java`: `TL_account.updateBusinessLocation` dikirim melalui `sendRequest` | Data profil disimpan melalui server; tidak dapat dianggap client-only |
| Opening Hours | `Business/OpeningHoursActivity.java`: `TL_account.updateBusinessWorkHours` | Server-dependent |
| Greeting Messages | `Business/GreetMessagesActivity.java`: `TL_account.updateBusinessGreetingMessage` | Server-dependent |
| Away Messages | `Business/AwayMessagesActivity.java`: `TL_account.updateBusinessAwayMessage` | Server-dependent |
| Business Intro / Start Page | `Business/BusinessIntroActivity.java`: `TL_account.updateBusinessIntro` | Server-dependent |
| Chatbots | `Business/ChatbotsActivity.java` mengirim update request; `BusinessChatbotController.java` memuat `TL_account.getConnectedBots` | Server-dependent dan melibatkan bot pihak ketiga |
| Business Links | `BusinessLinksActivity.java` menggunakan controller/model link Business; perlu telusuri implementasi `BusinessLinksController` sampai request sebelum menilai operasi CRUD satu per satu | Belum ditetapkan; bukan bukti client-only |
| Quick Replies | `Business/QuickRepliesController.java` memuat daftar dari cache lokal `business_replies`, tetapi juga melakukan fetch/sort/edit/delete/send melalui `TL_messages_*QuickReply*` dan update Greeting/Away melalui `TL_account.*` | Hybrid; cache lokal tidak berarti entitlement dan sinkronisasi bisa dihilangkan |

Business settings dibuka dari daftar fitur `PremiumPreviewFragment.java` hanya ketika `getUserConfig().isPremium()` true. Untuk membuka halaman secara lokal saja memang mungkin secara teknis, tetapi simpan/perubahan operasi di atas tetap divalidasi oleh Telegram. Menghapus guard UI tanpa hasil valid dari server hanya akan membuat layar dapat dibuka, bukan memastikan fitur Business benar-benar bekerja.

**Kesimpulan Business:** tidak ada dasar source untuk menyatakan seluruh Business dapat diaktifkan melalui local grant. Paling tidak, Location, Hours, Greeting, Away, Intro, dan Chatbots terbukti server-backed. Quick Replies adalah campuran local cache dan API Telegram, sehingga juga tidak boleh diklasifikasikan client-only.

### 10.3 Katalog Premium pada source saat ini lebih luas dari lima feature key Tele-ß

`PremiumPreviewFragment.java` mendefinisikan feature ID sampai `PREMIUM_FEATURE_RICH_EDITOR` dan katalog yang mencakup:

- Stories dan subfiturnya: stealth mode, view history, expiration duration, save to gallery, links/formatting, priority order, caption, quality.
- Limits dan upload/download: doubled limits, upload limit, download speed.
- Voice-to-text, translation, ads, reactions, stickers, emoji status, animated emoji/avatar, profile badge.
- Advanced chat management, app icons, wallpaper, name/profile colors, saved tags/folder tags.
- Last seen/read time, message privacy, disable sharing.
- Business: Location, Opening Hours, Quick Replies, Greeting, Away, Chatbots, Intro, Chat Links.
- Message effects, TODO/checklists, AI Editor, Rich Editor.

Lima key saat ini (`CUSTOM_THEMES`, `CHAT_CUSTOMIZATION`, `CUSTOM_UI`, `ADVANCED_DOWNLOADS`, `ADVANCED_PRIVACY`) tidak mencakup atau memetakan katalog ini secara granular. Sebelum implementasi, perlu dibuat registry Tele-ß per capability, bukan satu sakelar global.

### 10.4 Inventaris gate yang ditemukan di source root

Pencarian GitHub pada `master` menemukan 92 file hasil untuk pencarian `isPremium()` dan 26 file untuk `premiumFeaturesBlocked`. Ini adalah hasil pencarian terindeks, bukan jaminan hitungan total seluruh kemunculan. Daftar di bawah mengelompokkan call site yang berhasil ditemukan; tiap kelompok masih perlu dipasangkan dengan method operasi dan request terkait sebelum diubah.

| Kelompok | File contoh yang terverifikasi | Interpretasi |
|---|---|---|
| Gate umum / upsell | `PremiumPreviewFragment.java`, `SettingsActivity.java`, `PremiumFeatureBottomSheet.java` | Navigation/katalog/upsell; bukan satu-satunya enforcement |
| Limits folder/tag | `FiltersSetupActivity.java`, `FilterCreateActivity.java`, `DialogCellTags.java` | Sebagian limit lokal berbasis config, sebagian fitur warna/tag; perlu cek server limits untuk create/update |
| Translation | `TranslateController.java`, `TranslateButton.java`, `TranslateAlert3.java` | Gate akun Premium lokal di UI/controller; request translate tetap ke Telegram dan server dapat membatasi |
| Voice transcription | `TranscribeButton.java` | Request server dan trial/cooldown; tidak dapat dibuka hanya lewat local grant |
| Rich Editor | `ChatAttachAlertRichLayout.java`, `RichEditor.java`, `RichEditorToolbar.java` | UI lock dan format/payload pengiriman; hybrid dan perlu test server |
| Stickers / reactions | `StickerCell.java`, `StickerEmojiCell.java`, `ReactionsContainerLayout.java`, `StickersActivity.java`, `TopicCreateFragment.java` | Campuran preview/selector/UI gate dan server-backed document/reaction data |
| Privacy | `PrivacyControlActivity.java`, `PrivacySettingsActivity.java`, `MessagePrivateSeenView.java` | Beberapa kontrol memerlukan update privacy rules Telegram; server-dependent |
| Stories | `StoriesController.java`, `StealthModeAlert.java`, `SelfStoryViewsPage.java`, `Stories/recorder/*` | Story capabilities dan view history terkait API/server state; audit khusus diperlukan |
| Download/upload | `FileLoader.java`, `FileLoadOperation.java`, `FileUploadOperation.java`, `SearchViewPager.java` | Sebagian UI/download behavior; batas kecepatan dan kuota juga dipengaruhi konfigurasi/native/server |
| Profile appearance | `PeerColorActivity.java`, `ProfileActivity2.java`, `ImageReceiver.java`, `StatusBadgeComponent.java` | Ada state tampilan lokal namun warna/status/profile flags dapat disinkronkan ke server |
| Paid messages / gifts | `PrivacyControlActivity.java`, `GiftSheet.java`, `GiftPremiumBottomSheet.java` | Melibatkan Stars, transaksi, atau state akun; jangan diperlakukan sebagai local-only |
| Auto-archive / chat management | `ArchiveSettingsActivity.java`, `SettingsActivity.java` | Ada kondisi lokal dan flag/config server; perlu klasifikasi per operasi |
| Ads | `VideoAds.java`, `SearchAdsInfoBottomSheet.java` | Pengaturan/penyembunyian iklan tidak boleh disamakan dengan server premium entitlement |

Selain gate `isPremium()`, `premiumFeaturesBlocked()` sendiri menyebar ke menu, settings, sticker/reactions, stories, privacy, limit sheet, dan premium presentation. Tidak aman untuk mengubah return value helper global tersebut menjadi “Freemium aktif”: dampaknya lintas fitur dan dapat mencampur kebijakan `premiumLocked` server.

### 10.5 Keputusan implementasi yang sudah bisa dipastikan

Belum ada patch feature-access yang dibuat dalam pembaruan ini. Berdasarkan bukti source:

1. **Jangan mengubah** `UserConfig.isPremium()`, `TLRPC.User.premium`, propagasi Premium ke native, `premiumFeaturesBlocked()`, atau limit Premium server menjadi true karena Tele-ß Freemium.
2. **Jangan membuka semua Business screen sekaligus**. Operasi penyimpanannya mengirim request Telegram dan server dapat menolak.
3. **Jangan menganggap forcePremium sebagai entitlement**. Pertahankan hanya untuk presentation jika memang diperlukan, tetapi jangan jadikan indikator fitur aktif.
4. **Bisa dipertimbangkan untuk implementasi terpisah**: fitur yang sepenuhnya lokal setelah ditelusuri sampai efek akhir (contoh kandidat appearance/UI customization). Namun daftar aman belum ditetapkan: setiap kandidat harus dibuktikan tidak menuntut Premium akun untuk fetch, persist, share, atau operasi server.
5. **Butuh uji runtime sebelum mengklaim sukses**: gunakan akun non-Premium pada build Tele-ß; jalankan tiap operasi end-to-end, periksa callback sukses/error dari server, tutup dan buka ulang app, restart proses, dan verifikasi state tetap konsisten.

### 10.6 Status pemeriksaan modul

Build project menggunakan modul media3 dari `TMessagesProj_Modules/media` melalui `settings.gradle` dan dependency `TMessagesProj/build.gradle`. Source modul tersebut merupakan fork/media library ExoPlayer; foldernya tidak mengandung referensi Premium/Business pada hasil pencarian repository. Dengan demikian, tidak ditemukan gate entitlement Telegram di modul media yang terindeks, dan modul ini bukan target utama patch Premium.

Batasan: GitHub code search mengembalikan pencarian source yang terindeks, bukan hasil ripgrep menyeluruh dari checkout. Karena itu, modul media dinilai **tidak ada indikasi Premium gate dari pencarian**, bukan dinyatakan telah diaudit setiap baris. Source modul lain tidak ditemukan di `TMessagesProj_Modules/` selain `media` pada tree saat ini.

### 10.7 Batas pekerjaan dan tindak lanjut

Audit ini sudah menemukan alasan teknis mengapa build #96 menampilkan sukses tetapi tidak membuka fitur: local grant belum terhubung ke gate pemakaian. Audit belum membuktikan satu paket penuh fitur Premium dapat dibuka secara legal/teknis oleh client-only entitlement. Fokus implementasi yang valid berikutnya adalah menyusun matriks per capability (gate UI, gate controller, data persistence, RPC, server acceptance, limit) lalu melakukan perubahan kecil pada capability yang memang lokal. Untuk fitur server-dependent, status server harus tetap dihormati; local patch tidak bisa menjamin operasi diterima.

## 11. Audit terarah berdasarkan seluruh fitur pada screenshot pengguna

Bagian ini memetakan item pada screenshot Premium umum dan Business. Klasifikasi client-side gate hanya berarti aplikasi mengunci UI/perilaku lokal; bukan bukti Telegram server menerima operasi. Server-dependent berarti operasi/data utama dikelola Telegram. Hybrid berarti keduanya berperan.

### 11.1 Fitur Premium umum

| Fitur screenshot | Source yang ditelusuri | Klasifikasi dan implikasi |
|---|---|---|
| Stories | StoriesController.java, StealthModeAlert.java, SelfStoryViewsPage.java, Stories/recorder/* | Hybrid/server-dependent. Story memakai banyak RPC TL_stories.*; caption dan expiration limits membaca isPremium(). Local grant tidak mengubah kuota server. Stealth/view-history terkait data view dan aturan privasi. |
| Unlimited Cloud Storage | FileLoader.java, FileLoadOperation.java, FileUploadOperation.java, ConnectionsManager.java, TgNetWrapper.cpp, native ConnectionsManager.cpp | Server/native-dependent. Cloud storage Telegram, upload-size dan download limits bukan storage lokal; tidak dapat dijamin unlimited dengan local preference. |
| Doubled Limits | MessagesController.java, FiltersSetupActivity.java, FilterCreateActivity.java, PremiumPreviewFragment.java, DoubledLimitsBottomSheet.java, native Premium.cpp | Hybrid/server-dependent. Config dan UI menampilkan limit, tetapi operasi server dapat memvalidasi channel, folder, pin, public link, dan akun. Mengubah angka lokal tidak menjamin server menerima limit lebih tinggi. |
| Telegram Business | Business source pada bagian 10.2 dan BusinessLinksController.java | Server-dependent/hybrid; rincian delapan fitur ada di 11.2. |
| Last Seen Times | PrivacyControlActivity.java, PrivacySettingsActivity.java, MessagePrivateSeenView.java | Server-dependent. Data last-seen/read-time dan aturan privasi berasal dari server; menghapus UI lock tidak menciptakan data yang tidak diberikan server. |
| Voice-to-Text | Components/TranscribeButton.java | Server-dependent. Mengirim TL_messages_transcribeAudio; source menangani trial/cooldown pada respons. Local grant tidak memberi kuota server. |
| Faster Download Speed | FileLoadOperation.java, FileLoader.java | Client + network/server constraints. FileLoadOperation memilih koneksi dan byte budget berdasar isPremium(). Kandidat perubahan client-side, tetapi tidak menjamin throughput; perlu benchmark dan uji stabilitas. |
| Real-Time Translation | TranslateController.java, TranslateButton.java, TranslateAlert3.java | Hybrid/server-dependent. Gate lokal isPremium(); request TL_messages_translateText dan TL_messages_translateRichMessage dikirim ke Telegram. UI unlock bukan bukti server mengizinkan. |
| Animated Emoji | SelectAnimatedEmojiDialog.java, StickersAlert.java, TopicCreateFragment.java, MediaDataController.java | Hybrid. Rendering di client, tetapi ketersediaan custom emoji/document dan pengiriman bergantung pada data/kebijakan Telegram. |
| Emoji Statuses | SetupEmojiStatusSheet.java, PeerColorActivity.java, ProfileActivity2.java | Hybrid/server-dependent. UI pemilih lokal, tetapi status profil/expiry/collectible disimpan sebagai state profil Telegram. |
| Tags in Saved Messages | SavedMessagesController.java, SearchTagsList.java, DialogCellTags.java, ReactionsContainerLayout.java | Hybrid. Ada gate isPremium() untuk tag; perlu verifikasi penuh apakah setiap operasi tag disimpan lokal atau disinkronkan. Belum aman disebut client-only. |
| Name and Profile Colors | PeerColorActivity.java, ProfileActivity2.java, StatusBadgeComponent.java | Hybrid. Preview/pemilihan client-side; penerapan warna profil dapat mengubah state profil server. |
| Wallpaper for Both Sides | ThemePreviewActivity.java dan alur chat theme/wallpaper | Belum dipastikan. Wallpaper lokal sendiri berbeda dari mengirim theme ke kedua pihak; request dan server acceptance perlu ditelusuri sebelum implementasi. |
| Profile Badge | StatusBadgeComponent.java, ProfileActivity2.java, UserConfig.java | Hybrid/server-dependent. Badge akun Telegram bukan sekadar ikon lokal. Tele-ß boleh punya badge merek sendiri, bukan menyamar sebagai Premium Telegram. |
| Paid Messages | PrivacyControlActivity.java dan Stars/payment controllers | Server/payment-dependent. Memerlukan Stars/transaksi/validasi server; bukan fitur yang bisa dijadikan gratis melalui local grant. |
| Disable Sharing | PrivacyControlActivity.java, ChatActivity.java, MessagesController.java | Server-dependent/hybrid. Pembatasan forward/save harus didukung server/platform; menghapus client gate tidak menjamin proteksi. |
| Advanced Chat Management | ArchiveSettingsActivity.java, SettingsActivity.java, MessagesController.java | Hybrid. Sebagian setting lokal; beberapa batas archive/folder dan sinkronisasi dipengaruhi config/server. Klasifikasi per subfitur diperlukan. |
| No Ads | VideoAds.java, SearchAdsInfoBottomSheet.java, PremiumPreviewFragment.java | Hybrid/server-dependent. Client bisa menyembunyikan sebagian tampilan iklan, tetapi sponsored messages dan distribusi iklan terkait server. |
| Premium App Icons | SettingsActivity.java, AppIconsSelectorCell.java | Client-side candidate. Launcher icon Android merupakan fungsi lokal; kandidat kuat untuk entitlement Freemium setelah manifest/alias dan aset diverifikasi. |
| Infinite Reactions | ReactionsContainerLayout.java, ReactionsDoubleTapManageActivity.java, reaction models | Hybrid/server-dependent. Selector dikunci oleh isPremium(); daftar reaksi dan pengiriman tetap terkait data/protokol Telegram. |
| Animated Profile Pictures | ImageReceiver.java, ProfileActivity2.java, profile media handling | Hybrid. Rendering animasi lokal; upload/media profil dan aturan profil bergantung server. |
| Premium Stickers | StickerCell.java, StickerEmojiCell.java, StickersAlert.java, MediaDataController.java | Hybrid/server-dependent. Rendering lokal, tetapi akses set/document, install, dan pengiriman mengikuti data/kebijakan Telegram. |
| Message Effects | ReactionsContainerLayout.java, CustomEmojiReactionsWindow.java, MessageSendPreview.java | Hybrid/server-dependent. Pemilihan/render lokal; payload, media, penerima, dan server menentukan hasil. |
| AI Tools | AIEditorAlert.java, TranslateController.java, BotWebViewContainer.java | Hybrid/server-dependent. Limit lokal dan layanan remote harus dipisahkan per alat/provider; local grant bukan kuota AI remote. |
| Formatting Tools | RichEditor.java, ChatAttachAlertRichLayout.java, MessagePreviewView.java | Hybrid. Editor/payload disusun client-side; format/payload khusus perlu diuji kompatibilitas server dan klien penerima. |
| Checklists | PremiumPreviewFragment.java, message/media models, checklist UI | Belum dipastikan sampai operasi. UI katalog tidak membuktikan operasi checklist lokal; telusuri payload, request, dan respons. |

### 11.2 Telegram Business sesuai screenshot

| Fitur | Jalur source/request | Klasifikasi |
|---|---|---|
| Location | LocationActivity.java → TL_account.updateBusinessLocation | Server-dependent |
| Opening Hours | OpeningHoursActivity.java → TL_account.updateBusinessWorkHours | Server-dependent |
| Quick Replies | QuickRepliesController.java → fetch/edit/delete/send TL_messages_*QuickReply*; cache juga disimpan di MessagesStorage | Hybrid; cache lokal tidak menghapus kebutuhan RPC |
| Greeting Messages | GreetMessagesActivity.java / controller → TL_account.updateBusinessGreetingMessage | Server-dependent |
| Away Messages | AwayMessagesActivity.java / controller → TL_account.updateBusinessAwayMessage | Server-dependent |
| Links to Chat | BusinessLinksController.java → get/create/edit/deleteBusinessChatLink | Server-dependent |
| Start Page | BusinessIntroActivity.java → TL_account.updateBusinessIntro | Server-dependent |
| Chatbots | BusinessChatbotController.java → getConnectedBots; ChatbotsActivity.java → updateConnectedBot | Server-dependent dan terhubung bot pihak ketiga |

Kesimpulan Business: semua delapan entri memerlukan operasi server untuk fungsi utamanya. Quick Replies memiliki cache lokal, tetapi daftar, shortcut, pesan, dan pengiriman tetap melibatkan RPC Telegram. Tidak ada dasar source untuk menjanjikan seluruh Business berjalan hanya dengan entitlement lokal.

### 11.3 Solusi teknis Tele-ß

**A. Tele-ß Native (client-only).** Buat registry capability lokal yang granular. Implementasikan hanya operasi yang sepenuhnya berjalan di perangkat. Kandidat kuat pertama dari screenshot adalah Premium App Icons. Tema/UI customization dan sebagian formatting dapat menjadi kandidat setelah persistensi dan payload diuji. Simpan entitlement lokal secara durable dan baca ulang saat Activity/proses dibuat kembali. Ini entitlement instalasi Tele-ß, bukan entitlement akun Telegram.

**B. Telegram API (server-dependent).** Jika Telegram server memeriksa status Premium, client Tele-ß tidak dapat menjamin fitur itu aktif hanya dengan mengubah Java/Kotlin. Jalur yang valid adalah akun memperoleh hak melalui mekanisme resmi Telegram. Tele-ß harus mempertahankan status akun asli dan tidak mengubah UserConfig.isPremium(), TLRPC.User.premium, native premium flag, server limit, atau request identity untuk berpura-pura menjadi pelanggan.

**C. Provider lokal/mandiri.** Tele-ß dapat membuat alternatif yang diberi label Tele-ß: transkripsi memakai model/provider pilihan pengguna, terjemahan memakai engine/provider sendiri, storage tambahan memakai storage milik pengguna, dan quick-reply template lokal. Ini fitur pengganti Tele-ß, bukan unlock layanan Telegram Premium.

### 11.4 Prioritas implementasi

| Prioritas | Capability | Keputusan |
|---|---|---|
| P0 | Durable entitlement + granular feature registry | Fondasi wajib; jangan gunakan satu flag generik untuk seluruh katalog. |
| P1 | Premium App Icons | Implementasi lokal memungkinkan setelah manifest/alias/aset diverifikasi. |
| P1 | Theme/UI customization | Implementasikan hanya pengaturan yang benar-benar lokal. |
| P1 | Formatting/checklist editor | Audit payload dan kompatibilitas dahulu; implementasikan editor Tele-ß/format standar bila cocok. |
| P2 | Faster Download Speed | Perubahan concurrency/byte budget client perlu benchmark; tidak menjamin unlimited atau throughput server. |
| P2 | Quick Replies lokal | Bisa dibuat sebagai fitur Tele-ß mandiri; tidak otomatis menyinkronkan Business Quick Replies Telegram. |
| P2 | Voice-to-Text/Translation | Sediakan provider alternatif atau BYO provider, bukan bypass kuota Telegram. |
| P3 | Stories, limits, Business, Last Seen, Reactions, Premium Stickers, Paid Messages, Disable Sharing, No Ads, profile status | Server-dependent/hybrid; tidak dapat dijanjikan fully unlocked oleh local Freemium tanpa otorisasi server. |

### 11.6 Implementasi awal Theme/UI Tele-ß

Pada commit `015d4675468dca155a383caff132f5bdb6e252dc`, patch Freemium menambahkan satu gate granular pada `ThemePreviewActivity.applyWallpaperBackground(boolean forBoth)`:

- Mengizinkan penerapan wallpaper untuk akun sendiri melalui entitlement lokal `CHAT_CUSTOMIZATION`.
- Tetap mempertahankan gate Telegram Premium untuk menerapkan wallpaper yang sama ke kedua pihak (`forBoth`).
- Tidak mengubah `UserConfig.isPremium()`, `TLRPC.User.premium`, minimum boost channel/grup, maupun request Telegram.
- Tidak membuka batas wallpaper yang ditentukan level boost channel/grup.

Ini implementasi terbatas, bukan pembukaan semua Theme/UI. Tema global, accent color, theme editor, dan per-theme chat settings masih perlu dipetakan terpisah. Uji wajib: akun non-Premium dengan Freemium aktif, ubah wallpaper untuk diri sendiri, keluar/masuk chat, restart aplikasi, dan pastikan pilihan tetap terpasang. Uji `forBoth` dan kanal/grup ber-boost tetap mengikuti batas Telegram.

### 11.5 Mengapa belum ada patch gate pada commit audit ini

Melepas gate UI sebelum menelusuri operasi akhir akan mengulang masalah build #96: UI terbuka, tetapi operasi bisa ditolak, tidak tersimpan, atau tidak tersinkron. Karena targetnya fitur yang benar-benar bekerja, tiap capability harus memiliki bukti entry point → gate → controller → persistence → RPC (jika ada) → respons sukses → reload/restart. Audit ini menyimpulkan bahwa tidak mungkin menjamin seluruh fitur pada screenshot berfungsi sebagai Telegram Premium hanya dengan patch client Tele-ß. Sebagian dapat dibuat sebagai fitur lokal Tele-ß; sebagian memerlukan entitlement Telegram resmi; sebagian lain dapat diganti dengan provider/fitur mandiri yang berbeda dari layanan Telegram.
