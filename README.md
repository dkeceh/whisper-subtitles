# Whisper Subtitles

Subtitle otomatis untuk **DaVinci Resolve (free)** — berjalan sepenuhnya offline di komputer Anda.

## Fungsi

Mengubah audio pada timeline Resolve menjadi track subtitle secara otomatis: audio diekstrak, ditranskripsi oleh model Whisper (faster-whisper), lalu hasilnya diimpor kembali sebagai track subtitle di timeline — plus file `.srt` untuk cadangan.

Tidak memerlukan DaVinci Resolve Studio, akun cloud, atau koneksi internet (kecuali saat unduh model pertama kali).

## Fitur

- **Offline & gratis** — bekerja di DaVinci Resolve free, tanpa layanan cloud
- **Form pengaturan** — pilihan model (`tiny` … `large-v3`), bahasa (auto + 99 bahasa), cue per kalimat atau per kata, silence gap, maks huruf/kata
- **Timestamp per kata** — mode "word" membuat satu subtitle per kata dengan waktu mulai+akhir persis dari Whisper
- **Pecah per kalimat** — cue ditutup pada tanda baca (`.!?`) dan batas segmen Whisper
- **Ramah musik** — kalau VAD mendeteksi hampir tidak ada bicara (mis. lagu), otomatis diulang tanpa VAD
- **Progres nyata** — popup menampilkan unduhan model (`model.bin: 46%|...`) dan transkripsi (`0:57 / 1:37 transcribed`)
- **Hasil ganda** — track subtitle di timeline + file `.srt` di `~/Movies/DaVinci Subtitles/`
- **Log diagnostik** — `~/Movies/DaVinci Subtitles/last_run.log`

## Kebutuhan

| Komponen | Keterangan |
|---|---|
| macOS | Sudah dicoba di macOS Golden Gate 27.0.1, Apple M1 8GB |
| DaVinci Resolve | Sudah dicoba di DaVinci Resolve 21.0.2 Build 4 (free) |
| Python 3 | Dengan modul `tkinter` (ikut terpasang di installer python.org) |
| faster-whisper | `pip install faster-whisper` |
| ffmpeg | `brew install ffmpeg` |

> Catatan RAM: model `large-v3` butuh ~3GB dan bisa sesak bersama Resolve di mesin 8GB — gunakan `medium` atau `small` bila perlu.

## Cara Install

1. **Python 3** — unduh dari [python.org](https://www.python.org/downloads/) (saat ini teruji dengan Python 3.13; pastikan opsi tcl/tk dan IDLE tetap tercentang agar `tkinter` ikut terpasang).

2. **faster-whisper**:

   ```bash
   pip install faster-whisper
   ```

3. **ffmpeg** (via [Homebrew](https://brew.sh)):

   ```bash
   brew install ffmpeg
   ```

4. **Salin script** ke folder script Resolve:

   ```bash
   cp WhisperSubtitles.py \
     "~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Utility/"
   ```

   Jika folder `Fusion/Scripts/Utility` belum ada, buat dulu — lokasinya bisa berbeda tergantung versi Resolve, cek di menu `DaVinci Resolve > Settings > System > General` atau cari folder `Fusion/Scripts` di dalam `Application Support/Blackmagic Design/DaVinci Resolve`.

## Cara Menjalankan

1. Buka **DaVinci Resolve** dan pastikan timeline yang ingin disubtitle sedang terbuka (timeline aktif).
2. Buka menu **Workspace → Scripts → Utility → WhisperSubtitles**.
3. Isi form pengaturan lalu klik **Start**:
   - **Model** — `small` untuk mulai; `medium`/`large-v3` untuk akurasi lebih (terutama bahasa Indonesia)
   - **Language** — pilih bahasanya manual bila sudah tahu (mis. `id - Indonesian`); `auto` bisa salah pada musik
   - **Cue** — `sentence` per kalimat, atau `word` satu subtitle per kata
   - **Silence gap / Max words / Chars per line** — batas pemecahan cue (tidak berlaku di mode `word`)
4. Tunggu prosesnya — popup menampilkan progres; waktu pertama kali model akan diunduh (satu kali saja).
5. Selesai: subtitle muncul di timeline (track subtitle baru) dan file `.srt` tersimpan di `~/Movies/DaVinci Subtitles/`.

Bila terjadi kesalahan, periksa `~/Movies/DaVinci Subtitles/last_run.log`.

## Lisensi

MIT License — bebas dipakai, dimodifikasi, termasuk untuk komersial, tanpa jaminan.

Copyright (c) 2026 [dkeceh](http://github.com/dkeceh).
