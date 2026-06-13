#!/usr/bin/env python3
"""Replay a captured Meeting Brain session into the Coach overlay — no Tana needed.

A captured log is a recording. This streams one back into the log the overlay watches,
at a watchable cadence (header fast, one flag every few seconds so each lands and the
panel flashes, summary fast). Lets anyone SEE the meeting brain run before implementing
the `fetch_transcript_lines()` stub against their own Tana.

Usage (from this folder):
  python3 replay-coach-log.py                                  # sample → /tmp/meeting-brain.log
  python3 replay-coach-log.py path/to.cassette --flag-delay 4
  python3 replay-coach-log.py --log /tmp/coach.log             # if your viewer watches a different path

Keep --flag-delay >= ~3 (the overlay polls every 3s) for clean one-at-a-time reveals.
"""
import sys, time, argparse, os

FLAG_PREFIXES = ("→", "✓", "\U0001F4CB", "⏱", "\U0001F4CC", "\U0001F3AF",
                 "\U0001F91D", "\U0001F4CA", "\U0001F4D6", "\U0001F464", "⚡",
                 "❓", "\U0001F504", "\U0001F3C1")  # → ✓ 📋 ⏱ 📌 🎯 🤝 📊 📖 👤 ⚡ ❓ 🔄 🏁

HERE = os.path.dirname(os.path.abspath(__file__))

ap = argparse.ArgumentParser()
ap.add_argument("cassette", nargs="?", default=os.path.join(HERE, "sample-session.cassette"))
ap.add_argument("--log", default="/tmp/meeting-brain.log", help="log file the overlay watches")
ap.add_argument("--flag-delay", type=float, default=3.5, help="seconds between flag lines")
ap.add_argument("--header-delay", type=float, default=0.15, help="seconds between header lines")
ap.add_argument("--block-pause", type=float, default=1.2, help="pause after an 'analyzing' marker")
ap.add_argument("--no-truncate", action="store_true", help="append instead of resetting the log")
args = ap.parse_args()

with open(args.cassette, encoding="utf-8") as f:
    lines = [ln.rstrip("\n") for ln in f]

if not args.no_truncate:
    open(args.log, "w").close()

def emit(line):
    with open(args.log, "a", encoding="utf-8") as f:
        f.write(line + "\n")

in_summary = False
flags = 0
for line in lines:
    emit(line)
    s = line.strip()
    if "SESSION SUMMARY" in s:
        in_summary = True
    if in_summary:
        time.sleep(0.15)
    elif s.startswith(FLAG_PREFIXES):
        flags += 1
        print(f"  flag {flags}: {s[:60]}")
        time.sleep(args.flag_delay)
    elif "analyzing" in s:
        time.sleep(args.block_pause)
    else:
        time.sleep(args.header_delay)

print(f"replay complete — {flags} flags streamed to {args.log}")
