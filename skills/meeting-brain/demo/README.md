# See the Meeting Brain run — without wiring Tana

Watch a full Meeting Brain session animate in the Coach overlay using a **captured sample** —
no Tana connection, no `fetch_transcript_lines()` stub required. Good for a 60-second "does this
actually work?" before you invest in the real wiring.

It replays `sample-session.cassette` — a fictional **"Q3 Roadmap Sync"** in the
[demo workspace](../../../demo-workspace/DEMO-WORKSPACE.md) (Riya / Tom / Maya, Product) — into the
log the overlay watches.

## Run it

```bash
# 1. Start a viewer (pick one):
swiftc -O ../coach-popup.swift -o /tmp/Coach && /tmp/Coach     # the ⚡ menu-bar overlay (macOS)
#   …or, any OS:  tail -f /tmp/meeting-brain.log

# 2. Replay the sample (from this folder):
python3 replay-coach-log.py
```

Flags stream in one-by-one (~60s), ending with the session summary. Pace knobs:
`--flag-delay 2.5` (snappier) … `5` (slower). If your viewer watches a different path, pass
`--log /tmp/coach.log`.

## Then make it real

Once you implement `fetch_transcript_lines()` in [`../meeting-brain.py`](../meeting-brain.py),
the same kind of flags come from **your own live Tana transcript** instead of this cassette —
see the parent [SKILL.md](../SKILL.md).
