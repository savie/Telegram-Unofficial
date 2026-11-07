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
