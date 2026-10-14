# Whisper Subtitles

Automatic subtitles for **DaVinci Resolve (free)** — runs fully offline on your machine.

> **Not compatible with DaVinci Resolve 21.1 (free).**
> In 21.1, Blackmagic moved *all* Python scripting to the Studio edition —
> release notes: *"We have moved the ability to script in Python to the Studio
> version."* Free 21.1 no longer lists `.py` files in Workspace → Scripts
> (Lua still works, but is sandboxed: no file IO, no subprocess), and the
> external scripting API remains Studio-only. This script runs on
> **21.0.x and older free** (tested on 21.0.2). Options on 21.1: stay on
> 21.0.x, buy Studio, or wait for the planned CLI + Lua pipeline.

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

- **Offline & free** — works in DaVinci Resolve free (21.0.x only, see note above), no cloud services
- **Settings form** — model (`tiny` … `large-v3`, plus `large-v3-turbo`), language (auto + 99 languages), cue per sentence or per word, silence gap, max words/chars
- **Three outputs** — subtitle track + `.srt` file every run; optional Text+ clips, with karaoke next-line preview when a second template is set (see below)
- **Text+ mode** — each cue becomes one Text+ clip on a new video track, copied from a template you design once in the Media Pool (fonts, colors, position all follow the template)
- **Word-level timestamps** — "word" mode creates one subtitle per word with exact start/end times from Whisper
- **Sentence splitting** — cues close on punctuation (`.!?`) and Whisper segment boundaries
- **Music friendly** — if VAD finds almost no speech (e.g. a song), it automatically retries without VAD
- **Real progress** — popup shows model download (`model.bin: 46%|...`) and transcription (`0:57 / 1:37 transcribed`)
- **Diagnostic log** — `~/Movies/DaVinci Subtitles/last_run.log`

## Requirements

| Component | Notes |
|---|---|
| macOS | Tested on macOS Golden Gate 27.0.1, Apple M1 8GB |
| DaVinci Resolve | Tested on 21.0.2 Build 4 (free). **Does not work on 21.1+ free** (Python scripting moved to Studio) |
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
   - **Output** — `subtitle` (default) or `textplus`; for Text+, enter the template name, and optionally a preview template to enable karaoke mode (see below)
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
- Because every clip is a copy of the same template, changing the look later is easy: adjust the template's style, or edit any single clip independently.

> Note: Text+ clips are *not* subtitles in Resolve's sense — they won't be burned in as a subtitle track or exported via *Export Subtitle*. Use them for the visual look; keep the `.srt`/subtitle track for the text data.

### Karaoke next-line preview (Text+ mode)

When you fill in *Text+ preview template* in the form, Text+ mode also adds a read-ahead preview: for every subtitle line, a second Text+ clip (copied from that second template) shows the *next* line's text for the same duration — like following lyrics. Style the preview however you want via that second Media Pool template (dimmer, lower, smaller). Leave the field empty for plain Text+ mode (no preview). The last line has no preview.

## License

MIT License — free to use, share, and modify, including commercial use, without warranty.

Copyright (c) 2026 [dkeceh](http://github.com/dkeceh).
