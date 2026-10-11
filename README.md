# Whisper Subtitles

Automatic subtitles for **DaVinci Resolve (free)** — runs fully offline on your machine.

## Function

Reads the audio of the active timeline, transcribes it with a Whisper model (faster-whisper), and produces subtitles for that timeline. The pipeline is:

1. All audio clips on the timeline are mixed into one temporary audio file (timing preserved).
2. The audio is transcribed offline — the text, per-word timestamps, and language detection all happen on your machine.
3. The result is written out in up to three forms:
   - **Subtitle track** — a normal Resolve subtitle track on the timeline, ready to burn in on the Deliver page.
   - **`.srt` file** — always saved to `~/Movies/DaVinci Subtitles/` as a portable copy (backup, re-import, upload to YouTube, etc.).
   - **Text+ clips** (optional) — one Text+ clip per subtitle line on a new video track, for fully stylized subtitles.

No DaVinci Resolve Studio, cloud account, or internet connection required (except for the one-time model download).

## Features

- **Offline & free** — works in DaVinci Resolve free, no cloud services
- **Settings form** — model (`tiny` … `large-v3`, plus `large-v3-turbo`), language (auto + 99 languages), cue per sentence or per word, silence gap, max words/chars
- **Three outputs** — subtitle track + `.srt` file every run; optional Text+ clips (see below)
- **Text+ mode** — each cue becomes one Text+ clip on a new video track, copied from a template you design once in the Media Pool (fonts, colors, position, animation all follow the template)
- **Animated captions** — optional *Animation* in Text+ mode: `none`, `fade` (fade in/out + slide up), or `word pop` (karaoke-style — each word pops bigger then settles, staggered left to right); built-in keyframes, no macro needed
- **Word-level timestamps** — "word" mode creates one subtitle per word with exact start/end times from Whisper
- **Sentence splitting** — cues close on punctuation (`.!?`) and Whisper segment boundaries
- **Music friendly** — if VAD finds almost no speech (e.g. a song), it automatically retries without VAD
- **Lyrics alignment** — optional lyrics file: cue text and boundaries follow your lyric lines in order (markers like `[Intro]` / `[Verse]` are skipped); Whisper only supplies the timing, so the text is always your correct spelling
- **Real progress** — popup shows model download (`model.bin: 46%|...`) and transcription (`0:57 / 1:37 transcribed`)
- **Diagnostic log** — `~/Movies/DaVinci Subtitles/last_run.log`

## Requirements

| Component | Notes |
|---|---|
| macOS | Tested on macOS Golden Gate 27.0.1, Apple M1 8GB |
| DaVinci Resolve | Tested on DaVinci Resolve 21.0.2 Build 4 (free) |
| Python 3 | With the `tkinter` module (included in the python.org installer) |
| faster-whisper | `pip install faster-whisper` |
| ffmpeg | `brew install ffmpeg` |

> RAM note: `large-v3` needs ~3GB and can be tight next to Resolve on 8GB — try `large-v3-turbo` (nearly the same accuracy, ~8x faster, 1.6GB) or `medium`/`small` first.

## Installation

1. **Python 3** — download from [python.org](https://www.python.org/downloads/) (tested with Python 3.13; keep the tcl/tk and IDLE options checked so `tkinter` is installed).

2. **faster-whisper**:

   ```bash
   pip install faster-whisper
   ```

3. **ffmpeg** (via [Homebrew](https://brew.sh)):

   ```bash
   brew install ffmpeg
   ```

4. **Copy the script** into Resolve's script folder:

   ```bash
   cp WhisperSubtitles.py \
     "~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Utility/"
   ```

   If the `Fusion/Scripts/Utility` folder does not exist yet, create it — the exact path can vary by Resolve version; look for a `Fusion/Scripts` folder under `Application Support/Blackmagic Design/DaVinci Resolve`.

## How to Run

1. Open **DaVinci Resolve** and make sure the timeline you want subtitled is the active timeline.
2. Go to **Workspace → Scripts → Utility → WhisperSubtitles**.
3. Fill in the settings form and click **Start**:
   - **Model** — start with `small`; use `medium` or `large-v3-turbo` for better accuracy (especially Indonesian); full `large-v3` if you have the RAM
   - **Language** — pick the language manually when you know it (e.g. `id - Indonesian`); `auto` can be wrong on music
   - **Cue** — `sentence` per sentence, or `word` one subtitle per word
   - **Lyrics file** — optional, for songs: each subtitle line becomes one of your lyric lines, timed by Whisper (see *Using a Lyrics File* below)
   - **Output** — `subtitle` (default) or `textplus` (see the sections below); for Text+, enter the template name and pick **Animation** — `none` (static), `fade` (fade in/out + slide up), or `word pop` (karaoke-style per-word pop)
   - **Silence gap / Max words / Chars per line** — cue splitting limits (ignored in `word` mode)
4. Wait for the process — the popup shows progress; the first run downloads the model (one time only).
5. Done — check the timeline for the new subtitle track (and Text+ track if enabled), and the `.srt` file in `~/Movies/DaVinci Subtitles/`.

If something goes wrong, check `~/Movies/DaVinci Subtitles/last_run.log`.

### Output: Subtitle track

The default result is a regular Resolve **subtitle track**: every cue becomes one subtitle item, editable in the timeline like any other subtitle (double-click to fix wording, drag edges to adjust timing).

- **Burn-in**: include subtitles in the export via the Deliver page (Video → Subtitles → burn into video).
- **Separate file**: export the track anytime by right-clicking the subtitle track → *Export Subtitle…* (saves an `.srt`/`.vtt`).

### Output: The `.srt` file

Every run also saves a `.srt` file to `~/Movies/DaVinci Subtitles/`, named `<project>_<timeline>_<date-time>.srt`. The subtitle track on the timeline is a live copy — the `.srt` is your portable master:

- **Re-import later**: drag the `.srt` onto a timeline (or *File → Import → Timeline*), even on another project or another Resolve install.
- **Upload**: most platforms (YouTube, etc.) accept the `.srt` directly as a caption file.
- **Share / archive**: keep it next to the project file.

### Output: Text+ clips

Text+ mode turns every subtitle line into its own **Text+ clip** on a new video track above everything — ideal for styled subtitles (custom font, color, glow, position, animation) that you cannot get from a plain subtitle track.

**One-time setup — create the template:**

1. Open the Effects panel → *Titles* → drag a **Text+** onto any timeline.
2. Style it the way you want all subtitles to look (font, size, color, position in the Fusion/Inspector, etc.).
3. Right-click the Text+ clip in the timeline → **New Fusion Clip**. The clip appears in the Media Pool.
4. In the Media Pool, rename it (e.g. `SubtitleText`) — this name is what you type into the form's *Text+ template name* field.

**Each run in Text+ mode:**

- The normal subtitle track and `.srt` are still created (useful as reference/export).
- A new video track is added on top, containing one copy of your template per subtitle line, placed at the exact timing of each cue, with the text filled in automatically.
- Pick **Animation** to give every clip built-in keyframes, sized to each clip's length:
  - `none` — static captions, styled like the template.
  - `fade` — each caption fades in/out and slides up a little.
  - `word pop` — karaoke-style: the whole line appears, then each word pops (grows ~18% then settles) in turn, left to right. The stagger scales to the clip length, so short cues pop faster.
- Because every clip is a copy of the same template, changing the look later is easy: adjust the template's style, or edit any single clip independently.

> Note: Text+ clips are *not* subtitles in Resolve's sense — they won't be burned in as a subtitle track or exported via *Export Subtitle*. Use them for the visual look; keep the `.srt`/subtitle track for the text data.

### Using a Lyrics File (songs)

For music, Whisper's transcription is often full of mishearings. A lyrics file makes **your text** the subtitle — Whisper only supplies the timing.

**File format** — a plain `.txt` file, one lyric line per line, in song order:

```
[Intro]
[Verse 1]
Memandang langit dari atas bukit
Udara segar menyentuh kulit

[Chorus]
Oh indahnya alam ini
```

- Lines fully wrapped in brackets (`[Intro]`, `[Verse 1]`, `[Chorus]`, `[Outro]`) are skipped automatically — they won't appear as subtitles.
- Empty lines are ignored.
- Everything else becomes one subtitle line each, in order.

**How to use:**

1. In the form, click the **`...`** button next to **Lyrics file** and pick your `.txt` file (or type the full path).
2. Set **Language** to the song's language manually (e.g. `id - Indonesian`) — auto-detect is unreliable on music.
3. Start as usual. Each lyric line becomes one cue, timed by Whisper's word timestamps, matched to the lines in order.

**Good to know:**

- The matching is word-by-word and forgiving (a Whisper mishearing like "Semuat" still matches your "Semua"), but it works best when Whisper gets the words roughly right — a bigger model (`medium`/`large-v3-turbo`) helps.
- Works together with Text+ mode: the correct lyric text also ends up in the Text+ clips.
- If a line cannot be matched at all, it is placed as a 2-second cue right after the previous line so nothing is silently dropped — check those spots and nudge them if needed.
- The lyrics file is only used for timing/text alignment; the original `.srt` still contains exactly the lyric lines (without the bracket markers).

## License

MIT License — free to use, share, and modify, including commercial use, without warranty.

Copyright (c) 2026 [dkeceh](http://github.com/dkeceh).
