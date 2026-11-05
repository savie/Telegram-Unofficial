# Telegram Unofficial Client

Klien Android pihak ketiga untuk jaringan Telegram. Proyek ini menggunakan source upstream Telegram Android dan menambahkan fitur sisi-klien yang dikembangkan sendiri.

## Build APK

Jalankan workflow **Build Android APK** dari tab Actions. Workflow mengambil source upstream, menerapkan konfigurasi API milik pengembang, lalu membangun APK standalone.

Tambahkan repository secrets `TELEGRAM_API_ID` dan `TELEGRAM_API_HASH`. Dapatkan kredensial melalui https://my.telegram.org. Jangan memasukkan kredensial ke source code atau commit.

## Batas fitur

Fitur tambahan akan dibangun pada sisi aplikasi. Hak akses yang divalidasi server Telegram, termasuk entitlement Telegram Premium, tetap mengikuti status akun di server. Proyek ini tidak memalsukan status Premium.

## Upstream dan lisensi

- Upstream: https://github.com/TelegramOrg/Telegram-Android
- Lisensi upstream: GNU GPL v2 atau lebih baru.

Source turunan yang didistribusikan wajib memenuhi kewajiban lisensi upstream, termasuk penyediaan source code yang sesuai. Aplikasi ini bukan aplikasi resmi Telegram; identitas dan branding distribusi harus mengikuti ketentuan Telegram.