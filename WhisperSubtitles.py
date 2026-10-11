# -*- coding: utf-8 -*-
"""Whisper Subtitles - automatic subtitles for DaVinci Resolve, free & offline.

Usage: open a timeline, then Workspace > Scripts > Utility > WhisperSubtitles.
Result: a subtitle track on the timeline + a .srt file in ~/Movies/DaVinci Subtitles/
Last run log: ~/Movies/DaVinci Subtitles/last_run.log

MODEL   : tiny / base / small / medium / large-v3 / large-v3-turbo - larger = more accurate, slower
          (large-v3-turbo = nearly large-v3 accuracy at ~8x speed, good on 8GB RAM).
LANGUAGE: "" = auto detect, or a language code such as "id", "en".
"""
# Copyright (c) 2026 dkeceh (http://github.com/dkeceh)
#
# MIT License - free to use, share, and modify, including commercial use.
# The software is provided "as is", without warranty of any kind.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import traceback


def _utf8(stream):
    """Resolve may run with an ascii locale - force utf-8 so non-ascii text cannot explode."""
    try:
        if stream is not None and getattr(stream, "encoding", None) not in ("utf-8", "UTF-8"):
            return io.TextIOWrapper(stream.buffer, encoding="utf-8", errors="replace",
                                    line_buffering=True)
    except Exception:
        pass
    return stream


# Resolve sometimes provides no stdout/stderr for scripts.
if getattr(sys, "stdout", None) is None or getattr(sys, "stderr", None) is None:
    _log = open(os.path.join(tempfile.gettempdir(), "whisper_subtitles.log"), "a", encoding="utf-8")
    sys.stdout = sys.stdout or _log
    sys.stderr = sys.stderr or _log
sys.stdout = _utf8(sys.stdout)
sys.stderr = _utf8(sys.stderr)

# ============================ SETTINGS - safe to edit ============================
MODEL = "small"         # tiny / base / small / medium / large-v3 / large-v3-turbo (fast large)
LANGUAGE = ""           # "" = auto detect; "id" = Indonesian; "en" = English; "jv", "su", etc.
SILENCE_GAP = 0.6       # seconds. A pause longer than this splits the cue and hides the text
MAX_WORDS = 8           # maximum number of words per subtitle
UNIT = "sentence"       # "sentence" = per sentence (split when long) | "word" = one subtitle per word
LYRICS_PATH = ""        # optional lyrics file: cues follow its lines, [Intro]/[Verse] markers skipped
OUTPUT = "subtitle"     # "subtitle" = subtitle track | "textplus" = Text+ clips from a Media Pool template
TEXTPLUS_TEMPLATE = ""  # name of the Text+ template clip in the Media Pool (textplus mode)
MAX_CHARS_PER_LINE = {"vertical": 20, "horizontal": 42}  # chars per line (phone vs wide screen)
MAX_LINES = 2           # number of text lines per subtitle
# ===============================================================================

# Languages Whisper can recognize (~99). Shown as a dropdown; any code can also be typed.
LANGUAGES = [
    "auto - Auto detect", "id - Indonesian", "en - English", "jw - Javanese", "su - Sundanese",
    "ms - Malay", "af - Afrikaans", "am - Amharic", "ar - Arabic", "as - Assamese",
    "az - Azerbaijani", "ba - Bashkir", "be - Belarusian", "bg - Bulgarian", "bn - Bengali",
    "bo - Tibetan", "br - Breton", "bs - Bosnian", "ca - Catalan", "cs - Czech", "cy - Welsh",
    "da - Danish", "de - German", "el - Greek", "es - Spanish", "et - Estonian", "eu - Basque",
    "fa - Persian", "fi - Finnish", "fo - Faroese", "fr - French", "gl - Galician",
    "gu - Gujarati", "ha - Hausa", "haw - Hawaiian", "he - Hebrew", "hi - Hindi", "hr - Croatian",
    "ht - Haitian Creole", "hu - Hungarian", "hy - Armenian", "is - Icelandic", "it - Italian",
    "ja - Japanese", "ka - Georgian", "kk - Kazakh", "km - Khmer", "kn - Kannada", "ko - Korean",
    "lb - Luxembourgish", "lg - Ganda", "ln - Lingala", "lo - Lao", "lt - Lithuanian", "lv - Latvian",
    "mg - Malagasy", "mi - Maori", "mk - Macedonian", "ml - Malayalam", "mn - Mongolian",
    "mr - Marathi", "mt - Maltese", "my - Burmese", "ne - Nepali", "nl - Dutch",
    "nn - Norwegian Nynorsk", "no - Norwegian", "oc - Occitan", "pa - Punjabi", "pl - Polish",
    "ps - Pashto", "pt - Portuguese", "ro - Romanian", "ru - Russian", "sa - Sanskrit",
    "sd - Sindhi", "si - Sinhala", "sk - Slovak", "sl - Slovenian", "sq - Albanian",
    "sr - Serbian", "sn - Shona", "so - Somali", "sw - Swahili", "sv - Swedish",
    "ta - Tamil", "te - Telugu", "tg - Tajik",
    "th - Thai", "tk - Turkmen", "tl - Tagalog", "tr - Turkish", "ug - Uyghur", "uk - Ukrainian",
    "ur - Urdu",
    "uz - Uzbek", "vi - Vietnamese", "yi - Yiddish", "yo - Yoruba", "yue - Chinese (Cantonese)",
    "zh - Chinese (Mandarin)",
]


def language_label(code):
    for item in LANGUAGES:
        if item.split(" - ")[0] == code:
            return item
    return code or LANGUAGES[0]

# GUI apps (including Resolve) have a very short PATH, so look in absolute locations.
FFMPEG_CANDIDATES = ("/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg")
HF_HOME_OVERRIDE = "/Volumes/VGEN10S1T/models/Huggingface"
API_MODULES = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules"
OUT_DIR = os.path.expanduser("~/Movies/DaVinci Subtitles")
LOG_FILE = os.path.join(OUT_DIR, "last_run.log")
NOTIFY = False
REPORTED = False
PROGRESS = None
LOCKED = False
LOCK_FILE = os.path.join(OUT_DIR, ".whisper_running")

# Transcription runs in a python that has faster-whisper.
PHASE2_SRC = '''
import os, sys, traceback
print("python:", sys.version.split()[0], sys.executable, flush=True)
try:
    import json
    from faster_whisper import WhisperModel

    job = json.load(open(sys.argv[1]))

    def fmt(t):
        ms = int(round(t * 1000))
        h, ms = divmod(ms, 3600000)
        m, ms = divmod(ms, 60000)
        s, ms = divmod(ms, 1000)
        return "%02d:%02d:%02d,%03d" % (h, m, s, ms)

    model = WhisperModel(job["model"], device="cpu", compute_type="int8")
    print("model ready, starting transcription", flush=True)

    def run_transcribe(vad):
        segments, info = model.transcribe(job["wav"], language=job["lang"] or None,
                                          vad_filter=vad, word_timestamps=True,
                                          condition_on_previous_text=False)
        return list(segments), info

    segments, info = run_transcribe(True)
    total = getattr(info, "duration", 0) or 0

    def stamp(sec):
        return "%d:%02d" % (int(sec) // 60, int(sec) % 60)

    max_chars = job["max_chars"]
    line_width = job["line_width"]

    def wrap(word_list):
        lines, cur = [], ""
        for w in word_list:
            if cur and len(cur) + 1 + len(w) > line_width:
                lines.append(cur)
                cur = w
            else:
                cur = w if not cur else cur + " " + w
        if cur:
            lines.append(cur)
        return "\\n".join(lines)

    def norm_word(text):
        return "".join(ch for ch in text.lower() if ch.isalnum())

    def read_lyrics(path):
        try:
            with open(path, encoding="utf-8", errors="replace") as handle:
                raw_lines = [l.strip() for l in handle]
        except OSError:
            return []
        return [l for l in raw_lines
                if l and not (l.startswith("[") and l.endswith("]"))]   # skip [Intro] [Verse] ...

    def align_lyrics(lines, segments):
        """Match each lyric line to whisper word timings, in order. Text = the lyric line."""
        words = [(norm_word(w.word), w.start, w.end)
                 for seg in segments for w in (seg.words or []) if (w.word or "").strip()]
        cues, wi, prev_end = [], 0, 0.0
        for line in lines:
            targets = [norm_word(t) for t in line.split() if norm_word(t)]
            if not targets:
                continue
            start = end = None
            ti, budget = 0, 12
            while ti < len(targets) and wi < len(words) and budget > 0:
                wt, ws, we = words[wi]
                tg = targets[ti]
                if wt == tg or (len(tg) >= 4 and (wt.startswith(tg) or tg.startswith(wt))):
                    if start is None:
                        start = ws
                    end = we
                    ti += 1
                    wi += 1
                elif ti + 1 < len(targets) and wt == targets[ti + 1]:
                    ti += 1                              # word missing from audio
                elif wi + 1 < len(words) and words[wi + 1][0] == tg:
                    wi += 1                              # extra word in audio
                else:
                    wi += 1                              # whisper misheard - skip it
                    budget -= 1
            if start is None:                            # no match at all - park after previous cue
                start = prev_end
                end = prev_end + 2.0
            cues.append([start, end, line.split()])
            prev_end = end
        return cues

    def build_cues(segments):
        lyrics_path = job.get("lyrics") or ""
        if lyrics_path:
            lines = read_lyrics(lyrics_path)
            if lines:
                print("lyrics: aligning %d lines from %s"
                      % (len(lines), os.path.basename(lyrics_path)), flush=True)
                return align_lyrics(lines, segments)
        cues = []          # [start, end, [word, ...]]
        cur = None
        count = 0
        per_word = job.get("unit") == "word"

        def tick(end_time):
            if count % 25 == 0:
                if total:
                    sys.stdout.write("\\r  %s / %s transcribed | %d words"
                                     % (stamp(end_time), stamp(total), count))
                else:
                    sys.stdout.write("\\r  %s transcribed | %d words"
                                     % (stamp(end_time), count))
                sys.stdout.flush()

        for seg in segments:
            for w in (seg.words or []):
                word = (w.word or "").strip()
                if not word:
                    continue
                if per_word:
                    cues.append([w.start, w.end, [word]])
                    count += 1
                    tick(w.end)
                    continue
                if cur and (w.start - cur[1] > job["gap"]
                            or len(" ".join(cur[2] + [word])) > max_chars
                            or len(cur[2]) >= job["max_words"]):
                    cues.append(cur)
                    cur = None
                if cur is None:
                    cur = [w.start, w.end, [word]]
                else:
                    cur[1] = w.end
                    cur[2].append(word)
                count += 1
                if word[-1:] in ".!?":   # sentence ended - close the cue even if short
                    cues.append(cur)
                    cur = None
                else:
                    tick(w.end)
            if cur:   # whisper segment = one sentence, close the cue here
                cues.append(cur)
                cur = None
        if cur:
            cues.append(cur)
        return cues

    cues = build_cues(segments)
    if sum(c[1] - c[0] for c in cues) < total * 0.15:  # VAD filtered nearly all - typical for music
        print("\\nVAD left almost no speech - retrying without it (music?)", flush=True)
        segments, info = run_transcribe(False)
        cues = build_cues(segments)
    if not cues:  # no word timestamps - fall back to raw segments
        cues = [[s.start, s.end, (s.text or "").split()] for s in segments]
    print("cues:", len(cues), flush=True)
    with open(job["srt"], "w", encoding="utf-8") as out:
        for index, (start, end, words) in enumerate(cues, 1):
            out.write("%d\\n%s --> %s\\n%s\\n\\n"
                      % (index, fmt(start), fmt(end), wrap(words)))
    print("language:", info.language, flush=True)
except Exception:
    traceback.print_exc()
    sys.exit(1)
'''

# Multi-field settings form, run as a separate process (has its own window).
FORM_SRC = '''
import json, sys
try:
    import tkinter as tk
    from tkinter import messagebox, ttk, filedialog
except Exception as exc:
    print(json.dumps({"error": "tkinter: %s" % exc}))
    sys.exit(1)

initial = json.loads(sys.argv[1])
root = tk.Tk()
root.title("Whisper Subtitles - Settings")
root.attributes("-topmost", True)
root.resizable(False, False)

box = ttk.Frame(root, padding=16)
box.grid(row=0, column=0)
ttk.Label(box, text="Automatic Subtitle Settings", font=("Helvetica", 14, "bold")).grid(
    row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
ttk.Label(box, text=initial["status"], foreground="#666666").grid(
    row=1, column=0, columnspan=2, sticky="w", pady=(0, 14))

def field(row, label, value):
    ttk.Label(box, text=label).grid(row=row, column=0, sticky="w", pady=4, padx=(0, 14))
    var = tk.StringVar(value=str(value))
    ttk.Entry(box, textvariable=var, width=26).grid(row=row, column=1, sticky="we", pady=4)
    return var

ttk.Label(box, text="Model").grid(row=2, column=0, sticky="w", pady=4, padx=(0, 14))
model = ttk.Combobox(box, values=["tiny", "base", "small", "medium", "large-v3", "large-v3-turbo"], state="readonly", width=24)
model.set(initial["model"])
model.grid(row=2, column=1, sticky="we", pady=4)
ttk.Label(box, text="Language").grid(row=3, column=0, sticky="w", pady=4, padx=(0, 14))
language = ttk.Combobox(box, values=initial["languages"], width=24)
language.set(initial["lang_display"])
language.grid(row=3, column=1, sticky="we", pady=4)
ttk.Label(box, text="Cue").grid(row=4, column=0, sticky="w", pady=4, padx=(0, 14))
unit = ttk.Combobox(box, values=["sentence - one subtitle per sentence",
                                 "word - one subtitle per word"], state="readonly", width=24)
unit.set("word - one subtitle per word" if initial.get("unit") == "word"
         else "sentence - one subtitle per sentence")
unit.grid(row=4, column=1, sticky="we", pady=4)
ttk.Label(box, text="Lyrics file (optional)").grid(row=5, column=0, sticky="w", pady=4, padx=(0, 14))
lyrics = tk.StringVar(value=initial.get("lyrics", ""))
ttk.Entry(box, textvariable=lyrics, width=26).grid(row=5, column=1, sticky="we", pady=4)
ttk.Button(box, text="...", width=3, command=lambda: lyrics.set(
    filedialog.askopenfilename() or lyrics.get())).grid(row=5, column=2, sticky="w", padx=(4, 0), pady=4)
gap = field(8, "Silence gap in seconds before text disappears", initial["gap"])
words = field(9, "Max words per subtitle", initial["words"])
chars = field(10, "Chars per line", initial["chars"])
ttk.Label(box, text="Output").grid(row=6, column=0, sticky="w", pady=4, padx=(0, 14))
output = ttk.Combobox(box, values=["subtitle - subtitle track (default)",
                                   "textplus - Text+ clips from a template"],
                      state="readonly", width=24)
output.set("textplus - Text+ clips from a template" if initial.get("output") == "textplus"
           else "subtitle - subtitle track (default)")
output.grid(row=6, column=1, sticky="we", pady=4)
ttk.Label(box, text="Text+ template name").grid(row=7, column=0, sticky="w", pady=4, padx=(0, 14))
template = tk.StringVar(value=initial.get("template", ""))
ttk.Entry(box, textvariable=template, width=26).grid(row=7, column=1, sticky="we", pady=4)
result = {}

def start():
    try:
        gap_value = float(gap.get().replace(",", "."))
        words_value = int(words.get())
        chars_value = int(chars.get())
        if gap_value <= 0 or words_value < 1 or chars_value < 5:
            raise ValueError
    except ValueError:
        messagebox.showerror("Whisper Subtitles",
                             "Gap, words, and chars must be valid numbers.", parent=root)
        return
    result.update(model=model.get(), lang=language.get().strip(), gap=gap_value,
                  words=words_value, chars=chars_value,
                  unit="word" if unit.get().startswith("word") else "sentence",
                  lyrics=lyrics.get().strip(),
                  output="textplus" if output.get().startswith("textplus") else "subtitle",
                  template=template.get().strip())
    root.destroy()

def cancel():
    result["cancelled"] = True
    root.destroy()

buttons = ttk.Frame(box)
buttons.grid(row=11, column=0, columnspan=3, sticky="e", pady=(16, 0))
ttk.Button(buttons, text="Cancel", command=cancel).grid(row=0, column=0, padx=(0, 8))
ttk.Button(buttons, text="Start", command=start).grid(row=0, column=1)
ttk.Label(box, text="MIT License - free to use and modify, no warranty",
          foreground="#999999").grid(row=12, column=0, columnspan=3, sticky="w", pady=(8, 0))
root.bind("<Return>", lambda e: start())
root.bind("<Escape>", lambda e: cancel())
root.update_idletasks()
root.geometry("+%d+%d" % ((root.winfo_screenwidth() - root.winfo_width()) // 2,
                          max((root.winfo_screenheight() - root.winfo_height()) // 2, 0)))
model.focus_set()
root.mainloop()
print(json.dumps(result))
'''


def applescript_string(text):
    """AppleScript tidak mengerti \\n - pecah jadi potongan yang disambung return."""
    return " & return & ".join(json.dumps(part) for part in str(text).split("\n"))


def run_text(cmd, timeout=900):
    """Run a command and decode its output as utf-8 (Resolve locale = ascii)."""
    result = subprocess.run(cmd, capture_output=True, timeout=timeout)
    return (result.returncode,
            result.stdout.decode("utf-8", "replace"),
            result.stderr.decode("utf-8", "replace"))


def log_line(text):
    try:
        os.makedirs(OUT_DIR, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as handle:
            handle.write("[%s] %s\n" % (time.strftime("%H:%M:%S"), text))
    except OSError:
        pass


def notify(text):
    log_line("notify: " + text)
    if not NOTIFY:
        return
    try:
        subprocess.run(["osascript", "-e",
                        "display notification %s with title \"Whisper Subtitles\""
                        % applescript_string(text)],
                       timeout=15)
    except Exception:
        pass


def dialog(text):
    """Blocking dialog. True = OK, False = Cancel. Failed to show = continue."""
    log_line("dialog: " + text.replace("\n", " | "))
    if not NOTIFY:
        return True
    try:
        code, _out, _err = run_text(
            ["osascript", "-e", "display dialog %s with title \"Whisper Subtitles\" "
             "buttons {\"Cancel\",\"OK\"} default button \"OK\"" % applescript_string(text)],
            timeout=3600)
        return code == 0
    except Exception:
        return True


def finish(message, failed=False):
    global REPORTED
    hide_progress()
    release_lock()
    print(message)
    log_line(("FAILED: " if failed else "") + message)
    if NOTIFY:
        dialog(message)
        REPORTED = True
    if failed:
        raise RuntimeError(message)


def find_ffmpeg():
    for exe in FFMPEG_CANDIDATES + (shutil.which("ffmpeg"),):
        if exe and os.path.exists(exe):
            return exe
    finish("ffmpeg not found in %s" % " or ".join(FFMPEG_CANDIDATES), failed=True)


def hf_home():
    """Cache HuggingFace yang bisa dibaca+ditulis (volume eksternal bisa saja tidak terpasang)."""
    for home in (os.environ.get("HF_HOME"), HF_HOME_OVERRIDE,
                 os.path.expanduser("~/.cache/huggingface")):
        if home and os.path.isdir(home) and os.access(home, os.R_OK | os.W_OK):
            return home
    return None


def child_env():
    """Resolve does not inherit the shell env, so HF_HOME is set manually."""
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    home = hf_home()
    if home:
        env["HF_HOME"] = home
    else:
        env.pop("HF_HOME", None)
    return env


def model_ready():
    home = hf_home()
    if not home:
        return False
    return os.path.isdir(os.path.join(home, "hub", "models--Systran--faster-whisper-%s" % MODEL))


def get_resolve():
    injected = globals().get("resolve")
    if injected is not None:
        return injected
    sys.path.insert(0, API_MODULES)
    import DaVinciResolveScript
    return DaVinciResolveScript.scriptapp("Resolve")


def collect_segments(timeline, fps):
    """[(file, seconds_from_timeline_start, seconds_into_source, duration_seconds), ...]"""
    first_frame = timeline.GetStartFrame()
    segments = []
    for track in range(1, timeline.GetTrackCount("audio") + 1):
        for item in timeline.GetItemListInTrack("audio", track) or []:
            pool_item = item.GetMediaPoolItem()
            path = pool_item.GetClipProperty("File Path") if pool_item else None
            if not path or not os.path.exists(path):
                continue
            segments.append((path,
                             ((item.GetStart() or first_frame) - first_frame) / fps,
                             float(item.GetSourceStartTime() or 0),
                             (item.GetDuration() or 1) / fps))
    segments.sort(key=lambda seg: seg[1])
    return segments


def extract_audio(segments, out_wav, ffmpeg):
    """Mix all audio clips into one 16kHz mono wav, positioned like the timeline."""
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-vn"]
    for path, _start, src_in, dur in segments:
        cmd += ["-ss", "%.3f" % max(src_in, 0.0), "-t", "%.3f" % max(dur, 0.05), "-i", path]
    chains, outs = [], []
    for index, (_path, start, _src_in, _dur) in enumerate(segments):
        chain = "[%d:a]aresample=16000,aformat=channel_layouts=mono" % index
        if start > 0:
            chain += ",adelay=%d:all=1" % round(start * 1000)
        chains.append(chain + "[a%d]" % index)
        outs.append("[a%d]" % index)
    chains.append("%samix=inputs=%d:normalize=0:duration=longest[out]"
                  % ("".join(outs), len(segments)))
    cmd += ["-filter_complex", ";".join(chains), "-map", "[out]",
            "-ar", "16000", "-ac", "1", out_wav]
    code, _out, err = run_text(cmd, timeout=600)
    if code or not os.path.exists(out_wav) or os.path.getsize(out_wav) < 1024:
        finish("ffmpeg failed: %s" % (err.strip()[-600:] or "empty output"), failed=True)


def find_python():
    tried = set()
    for exe in ("/Library/Frameworks/Python.framework/Versions/3.13/bin/python3",
                sys.executable, shutil.which("python3"), "/opt/homebrew/bin/python3"):
        if not exe or exe in tried:
            continue
        tried.add(exe)
        try:
            probe = subprocess.run([exe, "-c", "import faster_whisper"],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError:
            continue
        if probe.returncode == 0:
            return exe
    finish("faster-whisper not found. Run: pip3 install faster-whisper", failed=True)


def read_tail(path, limit=90):
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return " ".join(handle.read().split())[-limit:]
    except OSError:
        return ""


def hide_progress():
    global PROGRESS
    if PROGRESS is not None:
        try:
            PROGRESS.kill()
        except OSError:
            pass
        PROGRESS = None


def show_progress(text):
    """Process status popup. Re-shown every ~10 seconds with fresh content."""
    global PROGRESS
    hide_progress()
    if not NOTIFY:
        return None
    try:
        PROGRESS = subprocess.Popen(["osascript", "-e",
                                     "display dialog %s with title \"Whisper Subtitles\" "
                                     "buttons {} giving up after 120" % applescript_string(text)])
    except Exception:
        PROGRESS = None
    return PROGRESS


def progress_text(log_path):
    """Ambil baris progres terakhir dari log anak - bukan warning library."""
    try:
        with open(log_path, encoding="utf-8", errors="replace") as handle:
            raw = handle.read()
    except OSError:
        return ""
    marks = ("transcribed", "retrying", "cues:", "model ready", "language:")
    lines = [" ".join(l.split()) for l in raw.replace("\r", "\n").split("\n") if l.strip()]
    for line in reversed(lines):
        if any(mark in line for mark in marks):
            return line
    for line in reversed(lines):       # tqdm download bar: "model.bin: 45%|....| 210M/467M [00:12<...]"
        if "%|" in line:
            return line.split(" [")[0]
    return ""


def pid_alive(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    # zombies still answer signal 0 - ask ps for the real state
    try:
        state = subprocess.run(["ps", "-p", str(pid), "-o", "state="],
                               capture_output=True, timeout=5).stdout.strip()
    except Exception:
        return True
    return bool(state) and not state.startswith(b"Z")


def acquire_lock():
    """False when another transcription job is still running."""
    global LOCKED
    os.makedirs(OUT_DIR, exist_ok=True)
    try:
        pid = int(open(LOCK_FILE, encoding="utf-8").read().strip())
        stale = time.time() - os.path.getmtime(LOCK_FILE) > 6 * 3600
        if pid_alive(pid) and not stale:
            return False
    except (OSError, ValueError):
        pass
    try:
        with open(LOCK_FILE, "w", encoding="utf-8") as handle:
            handle.write(str(os.getpid()))
        LOCKED = True
    except OSError:
        pass
    return True


def release_lock():
    if not LOCKED:
        return
    try:
        os.remove(LOCK_FILE)
    except OSError:
        pass


def run_phase2(python, job_file, log_path):
    log_line("child python: %s" % python)
    notify("Transcribing with model '%s'..." % MODEL)
    with open(log_path, "w", encoding="utf-8") as log:
        proc = subprocess.Popen([python, "-u", "-c", PHASE2_SRC, job_file],
                                stdout=log, stderr=subprocess.STDOUT, env=child_env())
        next_note = time.time()
        while proc.poll() is None:
            time.sleep(2)
            if time.time() >= next_note:
                next_note = time.time() + 10
                status = progress_text(log_path) or "loading model"
                show_progress("TRANSCRIPTION IN PROGRESS\n%s" % status)
                notify("Still working... %s" % status)
    code = proc.returncode
    tail = read_tail(log_path, 400)
    log_line("exit code: %s | %s" % (code, tail or "empty log"))
    return code, tail


def import_srt(resolve, path):
    """Empty string = subtitles are on the timeline. Otherwise = a message for the user."""
    project = resolve.GetProjectManager().GetCurrentProject()
    pool = project.GetMediaPool()
    timeline = project.GetCurrentTimeline()
    # Resolve does not create a subtitle track from an .srt on its own - one must exist.
    if timeline is not None and timeline.GetTrackCount("subtitle") < 1:
        if not timeline.AddTrack("subtitle"):
            return "Could not create a subtitle track - create one manually and retry"
    try:
        items = pool.ImportMedia([path])
    except Exception as exc:
        return "ImportMedia error (%s) - use File > Import > Subtitle" % exc
    if not items:
        return "Resolve refused the .srt - use File > Import > Subtitle"
    try:
        if pool.AppendToTimeline(items):
            return ""
    except Exception:
        pass
    return "The SRT is in the Media Pool - drag it onto the timeline"


def srt_entries(path):
    """[(start_seconds, end_seconds, text), ...]"""
    def sec(stamp):
        hours, minutes, rest = stamp.split(":")
        seconds, millis = rest.split(",")
        return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000.0
    entries = []
    with open(path, encoding="utf-8") as handle:
        for block in handle.read().strip().split("\n\n"):
            lines = block.split("\n")
            if len(lines) < 3 or "-->" not in lines[1]:
                continue
            begin, end = lines[1].split(" --> ")
            entries.append((sec(begin.strip()), sec(end.strip()), " ".join(lines[2:])))
    return entries


def find_pool_clip(folder, name):
    for clip in folder.GetClipList() or []:
        if clip.GetName() == name:
            return clip
    for sub in folder.GetSubFolderList() or []:
        found = find_pool_clip(sub, name)
        if found:
            return found
    return None


def make_textplus(project, srt_path, template_name):
    """One Text+ clip per SRT cue, copied from a template clip in the Media Pool."""
    pool = project.GetMediaPool()
    timeline = project.GetCurrentTimeline()
    template = find_pool_clip(pool.GetRootFolder(), template_name)
    if template is None:
        return "Text+ template '%s' not found in the Media Pool." % template_name
    try:
        fps = float(project.GetSetting("timelineFrameRate"))
    except (TypeError, ValueError):
        return "Could not read the timeline frame rate."
    try:
        native_fps = float(template.GetClipProperty("FPS"))
    except (TypeError, ValueError):
        native_fps = fps
    ratio = native_fps / fps
    entries = srt_entries(srt_path)
    if not entries:
        return "The .srt has no cues - nothing to convert to Text+."
    if not timeline.AddTrack("video"):
        return "Failed to add a video track for Text+."
    track = timeline.GetTrackCount("video")
    base = timeline.GetStartFrame()
    infos = []
    for begin, end, _text in entries:
        infos.append({"mediaPoolItem": template, "startFrame": 0,
                      "endFrame": max(1, int(round((end - begin) * fps * ratio))),
                      "trackIndex": track,
                      "recordFrame": base + int(round(begin * fps)),
                      "mediaType": 1})
    items = pool.AppendToTimeline(infos)
    if not items or len(items) != len(entries):
        return "Text+ import: expected %d clips, got %s." % (
            len(entries), len(items) if items else 0)
    filled = 0
    for item, (_begin, _end, text) in zip(items, entries):
        try:
            comp = item.GetFusionCompByIndex(1)
            tools = (comp.GetToolList(False, "TextPlus") or {}) if comp else {}
            tool = None
            if hasattr(tools, "get"):          # python API returns {index: tool}
                tool = tools.get(1) or next(iter(tools.values()), None)
            elif tools:
                tool = tools[0]
            if tool is not None:
                tool.SetInput("StyledText", text)
                filled += 1
        except Exception as exc:
            log_line("textplus: could not set text on a clip (%s)" % exc)
    if filled != len(entries):
        return "Text+ clips added, but text was set on only %d of %d (check the template)." % (
            filled, len(entries))
    return ""


def safe_name(value):
    return "".join(char for char in str(value or "timeline")
                   if char.isalnum() or char in "-_ ").strip() or "timeline"


def ask_settings(chars_per_line):
    """Multi-field settings form (Tkinter). Fallback: single-field dialog."""
    global MODEL
    if not NOTIFY:
        return None
    payload = json.dumps({
        "model": MODEL, "lang_display": language_label(LANGUAGE), "languages": LANGUAGES,
        "gap": SILENCE_GAP, "words": MAX_WORDS, "chars": chars_per_line, "unit": UNIT,
        "lyrics": LYRICS_PATH, "output": OUTPUT, "template": TEXTPLUS_TEMPLATE,
        "status": ("model '%s' is already downloaded" % MODEL) if model_ready()
        else ("model '%s' will be downloaded now (one time)" % MODEL)})
    try:
        code, out, err = run_text([find_python(), "-c", FORM_SRC, payload], timeout=1800)
    except Exception as exc:
        code, out, err = 1, "", str(exc)
    answer = {}
    if code == 0 and out.strip():
        try:
            answer = json.loads(out.strip().splitlines()[-1])
        except ValueError:
            answer = {}
    if answer.get("cancelled"):
        return None
    if answer.get("model"):
        try:
            MODEL = answer["model"]
            lang = str(answer.get("lang_display", "")).split(" - ")[0].strip()
            return {"model": MODEL,
                    "lang": "" if lang.lower() in ("", "auto") else lang.lower(),
                    "gap": float(answer["gap"]), "words": int(answer["words"]),
                    "chars": int(answer["chars"]),
                    "unit": "word" if answer.get("unit") == "word" else "sentence",
                    "lyrics": str(answer.get("lyrics") or "").strip(),
                    "output": "textplus" if answer.get("output") == "textplus" else "subtitle",
                    "template": str(answer.get("template") or "").strip()}
        except (KeyError, TypeError, ValueError):
            pass
    log_line("Tkinter form failed (%s) - using fallback dialog"
             % (err.strip() or answer.get("error") or "unreadable output"))
    return ask_settings_line(chars_per_line)


def ask_settings_line(chars_per_line):
    """Settings dialog. Returns (model, language, gap, words, chars) or None if cancelled."""
    global MODEL
    if not NOTIFY:
        return None
    picked_code, picked_out, _err = run_text(
        ["osascript", "-e",
         'choose from list {"tiny","base","small","medium","large-v3","large-v3-turbo"} with title "Whisper Subtitles" '
         'with prompt "Model: larger = more accurate, slower; turbo = fast large-v3" default items {"%s"}' % MODEL])
    if picked_code != 0 or not picked_out.strip():
        return None
    MODEL = picked_out.strip()
    status = "already downloaded" if model_ready() else "will be downloaded (one time)"
    initial = "%s; %.1f; %d; %d" % (LANGUAGE or "auto", SILENCE_GAP, MAX_WORDS, chars_per_line)
    field_code, field_out, field_err = run_text(
        ["osascript", "-e",
         'display dialog "Model %s: %s. Enter 4 values separated by semicolons (;), in order: '
         'language (auto / id / en / jv / su), silence gap in seconds, words per subtitle, '
         'chars per line" with title "Whisper Subtitles" default answer "%s" '
         'buttons {"Cancel","Start"} default button "Start"'
         % (MODEL, status, initial)])
    if field_code != 0:
        finish("Settings dialog failed: %s" % (field_err.strip()[:200] or "no message"), failed=True)
    text = field_out.split("text returned:", 1)[-1].split(", button returned:")[0].strip()
    parts = [part.strip() for part in text.split(";")]
    if len(parts) != 4:
        finish("Enter 4 values separated by semicolons (;): language, gap, words, chars. "
               "Try again.", failed=True)
    language = parts[0]
    try:
        gap = float(parts[1].replace(",", "."))
        words = int(parts[2])
        chars = int(parts[3])
        if gap <= 0 or words < 1 or chars < 5:
            raise ValueError
    except ValueError:
        finish("Settings values are invalid. Try again.", failed=True)
    return {"model": MODEL, "lang": "" if language.lower() == "auto" else language,
            "gap": gap, "words": words, "chars": chars, "unit": "sentence",
            "lyrics": "", "output": "subtitle", "template": ""}


def main():
    global NOTIFY, MODEL, LANGUAGE, SILENCE_GAP, MAX_WORDS, MAX_CHARS_PER_LINE, UNIT, LYRICS_PATH
    global OUTPUT, TEXTPLUS_TEMPLATE
    NOTIFY = ("resolve" in globals())
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as handle:
        handle.write("\n=== start %s ===\n" % time.strftime("%Y-%m-%d %H:%M:%S"))

    if not acquire_lock():
        finish("A subtitle job is already running.\n"
               "Wait for the result popup, then run again.", failed=True)

    resolve = get_resolve()
    if resolve is None:
        finish("Resolve is not open. Run this from the Workspace > Scripts menu "
               "(external scripting is not available in the free version of Resolve).",
               failed=True)

    project = resolve.GetProjectManager().GetCurrentProject()
    timeline = project.GetCurrentTimeline() if project else None
    if timeline is None:
        finish("Open the timeline you want to subtitle first.", failed=True)

    try:
        fps = float(project.GetSetting("timelineFrameRate"))
    except (TypeError, ValueError):
        fps = 24.0

    segments = collect_segments(timeline, fps)
    if not segments:
        finish("No audio clips with readable source files on this timeline.", failed=True)

    duration = max(seg[1] + seg[3] for seg in segments)
    try:
        width, height = int(project.GetSetting("timelineResolutionWidth")), \
                        int(project.GetSetting("timelineResolutionHeight"))
    except (TypeError, ValueError):
        width, height = 0, 0
    orientation = "vertical" if height > width else "horizontal"
    choice = ask_settings(MAX_CHARS_PER_LINE[orientation])
    if choice is None:
        if NOTIFY:
            print("Cancelled by user.")
        return
    MODEL, LANGUAGE, SILENCE_GAP, MAX_WORDS, chars, UNIT, LYRICS_PATH = \
        choice["model"], choice["lang"], choice["gap"], choice["words"], \
        choice["chars"], choice["unit"], choice["lyrics"]
    OUTPUT = choice["output"]
    TEXTPLUS_TEMPLATE = choice["template"]
    if OUTPUT == "textplus" and not TEXTPLUS_TEMPLATE:
        finish("Text+ mode needs a template name.\n"
               "Create a Text+ template in the Media Pool and enter its name.", failed=True)
    if LYRICS_PATH and not os.path.isfile(LYRICS_PATH):
        finish("Lyrics file not found: %s" % LYRICS_PATH, failed=True)
    MAX_CHARS_PER_LINE = dict(MAX_CHARS_PER_LINE, **{orientation: chars})
    max_chars = MAX_CHARS_PER_LINE[orientation] * MAX_LINES
    model_status = "model '%s' is already downloaded" % MODEL if model_ready() \
        else "model '%s' will be downloaded now (one time)" % MODEL
    settings = ("Language: %s | Cue: %s | Silence gap: %.1fs | Words/cue: %d | Chars/line: %d"
                % (LANGUAGE or "auto", UNIT, SILENCE_GAP, MAX_WORDS,
                   MAX_CHARS_PER_LINE[orientation]))
    if LYRICS_PATH:
        settings += " | Lyrics: %s" % os.path.basename(LYRICS_PATH)
    if OUTPUT == "textplus":
        settings += " | Output: Text+ (%s)" % TEXTPLUS_TEMPLATE
    notify("Starting: %s | %s | %.0f seconds of audio" % (settings, model_status, duration))
    show_progress("TRANSCRIPTION IN PROGRESS\n"
                  "Model %s | %.0f s of audio | %d clips\n"
                  "If this popup has a button, ignore it - the job keeps running."
                  % (MODEL, duration, len(segments)))

    work = tempfile.mkdtemp(prefix="whisper_subs_")
    wav = os.path.join(work, "timeline.wav")
    notify("Extracting audio from %d clips..." % len(segments))
    log_line("ffmpeg: %s, wav: %s" % (find_ffmpeg(), wav))
    extract_audio(segments, wav, find_ffmpeg())

    srt = os.path.join(OUT_DIR, "%s_%s_%s.srt" % (
        safe_name(project.GetName()), safe_name(timeline.GetName()), time.strftime("%Y%m%d-%H%M%S")))
    job_file = os.path.join(work, "job.json")
    with open(job_file, "w", encoding="utf-8") as handle:
        json.dump({"wav": wav, "srt": srt, "model": MODEL, "lang": LANGUAGE,
                   "max_chars": max_chars, "max_words": MAX_WORDS, "gap": SILENCE_GAP,
                   "line_width": MAX_CHARS_PER_LINE[orientation], "unit": UNIT,
                   "lyrics": LYRICS_PATH}, handle)
    log_line("srt: %s" % srt)

    code, tail = run_phase2(find_python(), job_file, os.path.join(work, "progress.log"))
    if code != 0 or not os.path.exists(srt):
        if code is not None and code < 0:
            finish("Transcription was killed by the system (signal %d, usually not enough RAM). "
                   "Close other applications and try again." % -code, failed=True)
        finish("Transcription failed: %s" % (tail or "no message"), failed=True)
    if not open(srt, encoding="utf-8").read().strip():
        finish("No speech detected in the audio (music only?).\n"
               "Try setting Language to Indonesian in the settings form.", failed=True)

    problem = import_srt(resolve, srt)
    if not problem and OUTPUT == "textplus":
        problem = make_textplus(project, srt, TEXTPLUS_TEMPLATE)
    message = "Subtitles done: %s" % os.path.basename(srt)
    if problem:
        message += "\n" + problem
    finish(message, failed=bool(problem))


def run():
    global REPORTED
    try:
        main()
    except Exception as exc:
        text = traceback.format_exc()
        print(text)
        log_line("traceback: " + text.strip().splitlines()[-1])
        if not REPORTED:
            finish("Failed: %s" % exc)


# Resolve's script runner does not always set __name__ = "__main__".
if __name__ == "__main__" or "resolve" in globals():
    run()
