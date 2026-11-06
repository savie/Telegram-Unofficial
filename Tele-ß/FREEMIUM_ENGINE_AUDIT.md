# Tele-ß Freemium Engine — Catatan Implementasi

Tanggal: 6 November 2026
Repository: savie/Telegram-Unofficial
Branch: master
Baseline: 1ddf348f329e2c931089259527c2df89abd9c48b

## Status audit

Workflow `.github/workflows/build-android.yml` melakukan clone source upstream pada saat build:
`https://github.com/TelegramOrg/Telegram-Android.git`
dengan `--depth 1`, sehingga source upstream tidak tersimpan dalam repository fork.
Commit upstream yang teridentifikasi dari histori publik saat audit: `3de37c8cfb039452be7398909461da6288babf15` (13.1.1 / 7237). Karena workflow memakai branch default tanpa pin SHA, build berikutnya dapat mengambil source upstream yang berbeda.

Repository fork hanya berisi workflow dan README. Oleh karena itu implementasi harus dimasukkan sebagai patch deterministik dalam workflow, lalu diterapkan terhadap source upstream yang baru di-clone. Jangan menaruh source upstream lengkap ke fork.

## Temuan Premium

`UserConfig.isPremium()` membaca `currentUser.premium`, yaitu status Telegram yang disediakan server. `UserConfig.hasPremiumOnAccounts()` mengagregasi status akun-akun Telegram yang aktif. Dua metode itu adalah sumber status Premium Telegram dan tidak boleh diganti atau diubah.

Titik pemeriksaan yang diidentifikasi pada upstream 3de37c8:

- `UserConfig.java`: `hasPremiumOnAccounts()`, `getMaxAccountCount()`, dan `isPremium()`.
- `AppIconsSelectorCell.java`: ikon launcher yang ditandai premium; UI + pemilihan lokal.
- `LiteMode.java`: klasifikasi batas animasi premium/non-premium.
- `ArchiveSettingsActivity.java`: opsi auto-archive; server capability `autoarchiveAvailable` ikut dipakai.
- `SearchTagsList.java`: saved tags; guard interaksi UI.
- `PeerColorActivity.java`: warna profil akun; sebagian operasi menyimpan preferensi melalui request server, jadi tidak boleh dibuka client-only.
- `FiltersSetupActivity.java` dan `FilterCreateActivity.java`: folder tags dan batas folder; perlu periksa limit/server sebelum membuka akses.
- `DialogCellTags.java`: tampilan tag bergantung pada `folderTags` capability dan status Premium.
- `TranslateButton.java`: penerjemahan mengandalkan entitlement server atau `chat.autotranslation`.
- `PrivacyControlActivity.java`: aturan privasi dan gift preferences; perubahan dikirim ke Telegram server.
- `BotWebViewContainer.java`: ekspansi link tertentu dan markup media.
- `VideoAds.java`: perilaku iklan berdasar status Telegram dan server flags.
- `AvailableReactionCell.java`, `GiftSheet.java`, `TopicsFragment.java`: reaksi/gift/boost berkaitan dengan kemampuan dan validasi Telegram.
- `PremiumFeatureBottomSheet.java`: halaman informasi/upsell, bukan sumber entitlement lokal.

## Batas keamanan

Freemium tidak boleh memodifikasi `TLRPC.User.premium`, `UserConfig.isPremium()`, payload MTProto, limit server, flags capability, ataupun hasil request server. Jangan mengubah `hasPremiumOnAccounts()` untuk membuka batas jumlah akun karena itu mengubah kebijakan produk Telegram dan berpotensi membuat UI menyimpulkan entitlement server yang tidak ada.

Kategori yang aman untuk tahap awal adalah fitur yang sepenuhnya lokal dan tidak membutuhkan payload/limit server, misalnya pengaturan tema/customisasi UI lokal atau pilihan tampilan. Jangan membuka fitur upstream yang hanya terlihat client-side tetapi hasil akhirnya membutuhkan validasi server.

## Rencana integrasi aman

1. Tambahkan `TeleBetaFreemium.java` ke package `org.telegram.messenger` melalui patch workflow.
2. Engine menyimpan tier Tele-ß terpisah dari profil Telegram. Nilai awal selalu `FREE`; tidak boleh mengasumsikan `FREEMIUM` tanpa grant dari sistem Tele-ß yang terverifikasi.
3. API engine hanya mengevaluasi fitur lokal yang memang ditandai sebagai feature ID Tele-ß. Dilarang menjadi pengganti `UserConfig.isPremium()`.
4. Tambahkan controller terpisah untuk fitur lokal. Jangan melakukan substitusi global atas pemanggilan `isPremium()`.
5. Integrasikan UI/fitur lokal satu per satu. Untuk tahap pertama, buat fondasi engine saja dan jangan membuka gate Telegram Premium.
6. Pin upstream SHA pada workflow setelah disetujui agar patch dan audit selalu cocok dengan source yang sama.

## Validasi

Pada sesi audit ini:
- HEAD master berhasil dibaca.
- Workflow build berhasil dibaca.
- Run terbaru #23 sukses dan artifact APK tersedia, ukuran sekitar 69.2 MB.
- Upstream commit hash diidentifikasi dari source clone yang dipakai run via log: upstream fetch menggunakan branch default; commit hash historis yang ditemukan pada endpoint source adalah 3de37c8..., tetapi workflow belum mencatat SHA clone-nya. Anggap ini petunjuk versi, bukan bukti reproduksibilitas.
- Tidak ada Android SDK/Gradle workspace lokal di sesi ini; validasi build hanya bisa dilakukan lewat GitHub Actions setelah perubahan.

