# Whisper Subtitles

Automatic subtitles for **DaVinci Resolve (free)** — runs fully offline on your machine.

> **Resolve 21.1 (free)?** Python scripting was moved to Studio in 21.1
> ("We have moved the ability to script in Python to the Studio version"),
> so the `WhisperSubtitles.py` menu script only works on **21.0.x and older
> free**. On 21.1+ free use the **CLI + Lua pipeline** below — same results,
> three quick steps.

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

- **Offline & free** — works in DaVinci Resolve free, no cloud services (21.0.x: menu script; 21.1+: CLI + Lua pipeline)
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
| DaVinci Resolve | 21.0.x free (menu script) or 21.1+ free (CLI + Lua pipeline) |
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

### DaVinci Resolve 21.1+ (free): CLI + Lua pipeline

Python menu scripts are Studio-only from 21.1, but the same result takes three
steps: transcribe in the terminal, drag the `.srt` into Resolve, convert to
Text+ with a small Lua script. No Studio, no cloud.

**Install (once):**

1. **Python 3** — [python.org](https://www.python.org/downloads/) (3.11+).
2. **faster-whisper**: `pip3 install faster-whisper`
3. **ffmpeg**: `brew install ffmpeg`
4. **`srt2textplus.lua`** — copy into Resolve's script folder (create it if missing):

   ```bash
   cp srt2textplus.lua \
     "~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Utility/"
   ```

**Step 1 — transcribe the audio (terminal, no Resolve):**

```bash
python3 whisper_srt.py "path/to/your-file.mp4" --lang id
```

- **Choosing the file**: type the path, or just **drag the file from Finder
  onto the Terminal window** — the full path is pasted for you.
- **What it reads**: any media **ffmpeg** can open — video (`.mp4`, `.mov`,
  `.mkv`, `.m4v`, …) or audio only (`.mp3`, `.m4a`, `.wav`, `.aiff`,
  `.flac`, …). The video track is ignored; only audio is used.
- **Where the `.srt` lands**: next to the input file, same name
  (`your-file.srt`). Use `--out "somewhere/else.srt"` to put it anywhere.
- Useful options (all optional):

  | Option | Default | Notes |
  |---|---|---|
  | `--model` | `small` | `tiny`/`base`/`small`/`medium`/`large-v3`/`large-v3-turbo` — bigger = more accurate, slower |
  | `--lang` | auto | `id`, `en`, `jw`, `su`, … — set it manually for music, auto can guess wrong |
  | `--unit` | `sentence` | `word` = one subtitle per word (karaoke-style) |
  | `--gap` | `0.6` | pause (seconds) that starts a new cue |
  | `--words` | `8` | max words per cue |
  | `--chars` | `42` | max characters per line |

  First run downloads the model (one time, needs internet). Progress prints to
  the terminal. Full list: `python3 whisper_srt.py --help`.

**Step 2 — import into Resolve:**

1. Open the project and the timeline you want subtitled.
2. **Drag the `.srt` file from Finder onto the timeline** — Resolve creates a
   subtitle track with one item per cue, timed exactly as in the file.
   (The subtitle track and the Text+ track are independent: keep the subtitle
   track for export/burn-in, or delete it after converting if you only want
   Text+.)

**Step 3 — convert to Text+ (optional, styled subtitles):**

1. One-time: build a Text+ template clip in the Media Pool — see
   [Output: Text+ clips](#output-text-clips) above (style a Text+, make it a
   Fusion Clip, name it, e.g. `SubtitleText`). For karaoke preview, make a
   second, differently-styled template (dimmer/lower) — e.g. `SubtitlePreview`.
2. In the Media Pool, **select the template clip(s)**:
   - **1 clip** → plain mode: one Text+ per cue, text = the spoken line.
   - **2 clips** → karaoke mode: sorted by name — the first name becomes the
     **active line** (top track, matches the voice), the second becomes the
     **next-line preview** (lower track). The last cue has no preview.
3. Run **Workspace → Scripts → Utility → srt2textplus**. A new video track
   appears with one Text+ clip per cue, timing taken straight from the
   subtitle track. Progress/errors go to
   `~/Library/Application Support/Blackmagic Design/DaVinci Resolve/logs/ResolveDebug.txt`.

## License

MIT License — free to use, share, and modify, including commercial use, without warranty.

Copyright (c) 2026 [dkeceh](http://github.com/dkeceh).
