#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Standalone SRT generator - transcribe a media file to .srt without DaVinci Resolve.

Usage:
  python3 whisper_srt.py input.mp4
  python3 whisper_srt.py input.wav --model small --lang id
  python3 whisper_srt.py song.mp3 --lang id --out lyrics.srt --unit word

Requires: ffmpeg (brew install ffmpeg) and faster-whisper (pip3 install faster-whisper).
The resulting .srt can be dragged straight onto a Resolve subtitle track.
"""
# Copyright (c) 2026 dkeceh (http://github.com/dkeceh) - MIT License, see WhisperSubtitles.py
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import WhisperSubtitles as ws  # PHASE2_SRC, child_env, FFMPEG_CANDIDATES


def die(msg):
    sys.exit("error: %s" % msg)


def find_ffmpeg():
    for exe in ws.FFMPEG_CANDIDATES + (shutil.which("ffmpeg"),):
        if exe and os.path.exists(exe):
            return exe
    die("ffmpeg not found - install with: brew install ffmpeg")


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
    die("faster-whisper not found - run: pip3 install faster-whisper")


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe a media file to .srt (offline, no DaVinci Resolve).")
    parser.add_argument("input", help="media file (mp4, mov, mp3, wav, ...)")
    parser.add_argument("--model", default="small",
                        help="tiny / base / small / medium / large-v3 / large-v3-turbo")
    parser.add_argument("--lang", default="",
                        help='language code: id, en, jw, su, ... (default: auto detect)')
    parser.add_argument("--unit", default="sentence", choices=["sentence", "word"],
                        help="cue per sentence, or one cue per word")
    parser.add_argument("--gap", type=float, default=0.6,
                        help="pause (seconds) that splits a cue")
    parser.add_argument("--words", type=int, default=8, help="max words per cue")
    parser.add_argument("--chars", type=int, default=42, help="max chars per line")
    parser.add_argument("--out", default=None,
                        help="output .srt path (default: next to the input file)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        die("file not found: %s" % args.input)
    out = args.out or (os.path.splitext(args.input)[0] + ".srt")

    work = tempfile.mkdtemp(prefix="whisper_srt_")
    wav = os.path.join(work, "audio.wav")
    print("extracting audio...", flush=True)
    code = subprocess.call(
        [find_ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", "-i", args.input,
         "-vn", "-ar", "16000", "-ac", "1", wav])
    if code != 0 or not os.path.exists(wav):
        die("ffmpeg failed (code %d)" % code)

    job = os.path.join(work, "job.json")
    with open(job, "w", encoding="utf-8") as handle:
        json.dump({"wav": wav, "srt": out, "model": args.model, "lang": args.lang,
                   "max_chars": args.chars * 2, "max_words": args.words,
                   "gap": args.gap, "line_width": args.chars, "unit": args.unit}, handle)

    proc = subprocess.Popen(
        [find_python(), "-u", "-c", ws.PHASE2_SRC, job],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        env=ws.child_env(), text=True, encoding="utf-8", errors="replace")
    for line in proc.stdout:
        print(line, end="", flush=True)
    proc.wait()
    if proc.returncode != 0 or not os.path.exists(out):
        die("transcription failed (code %s)" % proc.returncode)
    print("srt: %s" % out)


if __name__ == "__main__":
    main()
