# Whisper Subtitles

Automatic subtitles for **DaVinci Resolve (free)** — runs fully offline on your machine.

## Function

Turns audio on a Resolve timeline into a subtitle track automatically: audio is extracted, transcribed with a Whisper model (faster-whisper), then imported back as a subtitle track on the timeline — plus a backup `.srt` file.

No DaVinci Resolve Studio, cloud account, or internet connection required (except for the one-time model download).

## Features

- **Offline & free** — works in DaVinci Resolve free, no cloud services
- **Settings form** — model choice (`tiny` … `large-v3`), language (auto + 99 languages), cue per sentence or per word, silence gap, max words/chars
- **Word-level timestamps** — "word" mode creates one subtitle per word with exact start/end times from Whisper
- **Sentence splitting** — cues close on punctuation (`.!?`) and Whisper segment boundaries
- **Music friendly** — if VAD finds almost no speech (e.g. a song), it automatically retries without VAD
- **Real progress** — popup shows model download (`model.bin: 46%|...`) and transcription (`0:57 / 1:37 transcribed`)
- **Dual output** — subtitle track on the timeline + `.srt` file in `~/Movies/DaVinci Subtitles/`
- **Diagnostic log** — `~/Movies/DaVinci Subtitles/last_run.log`

## Requirements

| Component | Notes |
|---|---|
| macOS | Tested on macOS Golden Gate 27.0.1, Apple M1 8GB |
| DaVinci Resolve | Tested on DaVinci Resolve 21.0.2 Build 4 (free) |
| Python 3 | With the `tkinter` module (included in the python.org installer) |
| faster-whisper | `pip install faster-whisper` |
| ffmpeg | `brew install ffmpeg` |

> RAM note: the `large-v3` model needs ~3GB and can be tight next to Resolve on an 8GB machine — use `medium` or `small` if needed.

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
   - **Model** — start with `small`; use `medium`/`large-v3` for better accuracy (especially Indonesian)
   - **Language** — pick the language manually when you know it (e.g. `id - Indonesian`); `auto` can be wrong on music
   - **Cue** — `sentence` per sentence, or `word` one subtitle per word
   - **Silence gap / Max words / Chars per line** — cue splitting limits (ignored in `word` mode)
4. Wait for the process — the popup shows progress; the first run downloads the model (one time only).
5. Done: subtitles appear on the timeline (new subtitle track) and the `.srt` file is saved in `~/Movies/DaVinci Subtitles/`.

If something goes wrong, check `~/Movies/DaVinci Subtitles/last_run.log`.

## License

MIT License — free to use, share, and modify, including commercial use, without warranty.

Copyright (c) 2026 [dkeceh](http://github.com/dkeceh).
