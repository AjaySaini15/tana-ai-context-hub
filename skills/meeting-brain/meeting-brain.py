#!/usr/bin/env python3
"""
Meeting Brain — Real-Time Meeting Co-Pilot for Tana + Claude.

Polls a Tana transcript node and, every interval, sends the newest transcript chunk
to Claude (via `claude -p`) with a cached static context file as the system prompt.
Claude returns 0-3 short flags — coaching cues, meeting-management nudges, and
strategic prompts — which are appended to a log file (and, on macOS, fired as
desktop notifications).

The static context (your meeting prep, push points, coaching watch list, suppression
rules, and the full flag taxonomy) is loaded once from CONTEXT_FILE, which the
companion SKILL.md writes before launching this script. Nothing about *what* to flag
is hard-coded here — the engine is generic; the context file is the brain.

Features preserved end-to-end:
  • Polling loop with chunk diffing (only the NEW transcript text is sent each cycle)
  • Skip-to-tail on a mid-meeting launch (don't churn through stale history)
  • Backlog fast-forward (poll fast and just consume until caught up, then resume)
  • Flag parsing, dedup, role-based suppression, and an end-of-session summary

╔══════════════════════════════════════════════════════════════════════════════╗
║  YOU MUST IMPLEMENT ONE FUNCTION: fetch_transcript_lines(node_id).             ║
║  It is a STUB below (search for "IMPLEMENT ME"). Until you wire it to your      ║
║  Tana, the loop runs but sees no transcript. See the comment block there.       ║
╚══════════════════════════════════════════════════════════════════════════════╝

Usage:
  python3 meeting-brain.py --transcript <nodeId> [--interval 60] [--from-start] [--wait]

Watch:
  tail -f /tmp/meeting-brain.log
"""

import subprocess, sys, time, os, argparse, signal

# ── Config constants (edit these to taste) ───────────────────────────────────
CLAUDE_CMD    = "claude"                      # how to invoke Claude Code on your PATH
CLAUDE_MODEL  = "sonnet"                       # model passed to `claude -p --model ...`
CONTEXT_FILE  = "./meeting-brain-context.md"   # written by SKILL.md, read once at start
LOG           = "/tmp/meeting-brain.log"       # flags are appended here; tail -f this
PID_FILE      = "/tmp/meeting-brain.pid"
STATE_LINES   = "/tmp/mb_last_lines.txt"       # persisted "lines seen" cursor (best-effort)

POLL_INTERVAL_DEFAULT = 60   # seconds between polls (overridable via --interval)
SILENCE_TIMEOUT_SEC   = 1200 # stop after this many seconds of no new content (20 min)

CATCHUP_INTERVAL = 10   # fast-forward polling interval (seconds) when behind
TAIL_LINES       = 100  # how many trailing lines to keep when skipping to the tail
CATCHUP_BATCH    = 60   # if a single cycle yields >= this many new lines, enter catchup
SKIP_TO_TAIL_MIN = TAIL_LINES + 50  # only skip-to-tail when the transcript is this large

CLAUDE_TIMEOUT   = 60   # seconds to wait on each `claude -p` call

# ── Args ─────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Meeting Brain — real-time meeting co-pilot")
parser.add_argument("--transcript", required=True, help="Tana transcript node ID")
parser.add_argument("--meeting-node", default="", help="Tana meeting node ID (optional; for your own chunk discovery)")
parser.add_argument("--interval", type=int, default=POLL_INTERVAL_DEFAULT, help=f"Poll interval in seconds (default: {POLL_INTERVAL_DEFAULT})")
parser.add_argument("--wait", action="store_true", help="Wait indefinitely for the transcript to appear")
parser.add_argument("--from-start", action="store_true", help="Process from the beginning (disable skip-to-tail)")
args = parser.parse_args()

TRANSCRIPT_ID = args.transcript
MEETING_NODE  = args.meeting_node
POLL_INTERVAL = args.interval
WAIT_MODE     = args.wait
FROM_START    = args.from_start

MAX_EMPTY = max(1, int(SILENCE_TIMEOUT_SEC / POLL_INTERVAL))  # empty polls before giving up

# ── State ────────────────────────────────────────────────────────────────────
flag_history    = []   # list of (timestamp, flag_type, topic, raw_line)
flag_counts     = {}   # {type: count} for the session summary
start_time      = time.time()
meeting_summary = ""   # priming summary produced by skip-to-tail


# ══════════════════════════════════════════════════════════════════════════════
#  IMPLEMENT ME — the only function you must write to make this run.
# ══════════════════════════════════════════════════════════════════════════════
def fetch_transcript_lines(node_id):
    """Return the transcript's lines, in order (oldest first, newest last), as a
    list of plain strings.

        >>> fetch_transcript_lines("demoTrnsQ3001")
        ["You: let's start with pricing.",
         "Riya: I'd push the one-pager to next week.",
         "You: I think maybe we can hold the date...", ...]

    The rest of this script treats the transcript purely as this growing list of
    strings: it diffs the list across polls to find the NEW lines, chunks them, and
    sends only the new text to Claude. It never needs to know how you got them.

    Pick ONE backing and implement it here. Options:

    1) TANA LOCAL DESKTOP SERVER
       If you run the Tana desktop app, it can expose a local HTTP server. Query the
       transcript node's children and return each child's text. Roughly:

           import json, urllib.request
           req = urllib.request.Request(
               "http://localhost:<port>/<your-get-children-endpoint>",
               data=json.dumps({"nodeId": node_id}).encode(),
               headers={"Authorization": "Bearer <token>",
                        "Content-Type": "application/json"})
           data = json.loads(urllib.request.urlopen(req, timeout=15).read())
           return [c["name"] for c in data.get("children", []) if c.get("name")]

    2) AN MCP BRIDGE
       Call your Tana MCP server's get_children on `node_id` and return each child's
       text. (The other skills in this repo use the MCP server `mcp__tana-local__*`,
       e.g. mcp__tana-local__get_children.) Shell out to whatever CLI/bridge exposes
       your MCP tools, parse the JSON, and return the list of child strings.

    3) AN EXPORTED / SYNCED TRANSCRIPT FILE  (easiest way to test the loop)
       If your transcript is mirrored to a local file that grows as the meeting runs:

           path = os.path.expanduser(f"~/tana-transcripts/{node_id}.txt")
           if not os.path.exists(path):
               return []
           with open(path, "r", encoding="utf-8") as fh:
               return [ln.rstrip("\\n") for ln in fh if ln.strip()]

    Until you implement this, the function returns [] and the loop simply waits.
    """
    # --- STUB: replace this with one of the implementations above. ---
    return []
# ══════════════════════════════════════════════════════════════════════════════


# ── Static context ─────────────────────────────────────────────────────────────
def load_static_context():
    if not os.path.exists(CONTEXT_FILE):
        write_log(f"  ERROR: {CONTEXT_FILE} not found. The SKILL.md orchestration should create it before starting.")
        sys.exit(1)
    with open(CONTEXT_FILE, "r", encoding="utf-8") as f:
        return f.read()


# ── Skip-to-tail priming ───────────────────────────────────────────────────────
def prime_from_tail(lines):
    """Given the full transcript lines so far, ask Claude to summarize the tail.
    Returns (summary_text, skip_index) where skip_index = number of lines to treat
    as already-seen so the live loop starts at the edge."""
    total = len(lines)
    skip_index = max(0, total - TAIL_LINES)
    tail_lines = lines[skip_index:]
    tail_text = " ".join(tail_lines).strip()
    if not tail_text:
        return "", skip_index

    write_log(f"  SKIP-TO-TAIL: {total} lines so far, skipping to line {skip_index}")
    write_log(f"  Priming from the last {len(tail_lines)} lines ({len(tail_text)} chars)...")

    prime_prompt = f"""TRANSCRIPT EXCERPT (the last {len(tail_lines)} segments of an ongoing meeting):
{tail_text[:6000]}

Summarize in 3-5 bullet points:
- What topics have been discussed
- Key decisions or commitments made
- What is being discussed right now
- Any open questions or unresolved threads

Be concise. This summary will be used as context for real-time meeting assistance."""

    try:
        r = subprocess.run(
            [CLAUDE_CMD, "-p", "--system-prompt",
             "You are summarizing a meeting transcript excerpt. Output only the bullet-point summary, nothing else.",
             "--model", CLAUDE_MODEL, prime_prompt],
            capture_output=True, text=True, timeout=CLAUDE_TIMEOUT
        )
        if r.returncode == 0 and r.stdout.strip():
            summary = r.stdout.strip()
            write_log(f"  PRIMED: {len(summary)} char summary")
            return summary, skip_index
    except Exception as e:
        write_log(f"  [Prime error] {e}")

    return "", skip_index


# ── Claude analysis ──────────────────────────────────────────────────────────
def analyze(new_text, static_context, context_summary=""):
    """Call Claude via `claude -p` with the static context file as the system prompt."""
    history_text = "\n".join(entry[3] for entry in flag_history[-5:]) if flag_history else "(none yet)"

    summary_block = ""
    if context_summary:
        summary_block = f"""MEETING SO FAR (summary of earlier discussion):
{context_summary}

"""

    user_msg = f"""{summary_block}NEW TRANSCRIPT ({len(new_text)} chars):
{new_text[:3000]}

LAST 5 FLAGS (do not repeat the same type+topic within 5 minutes):
{history_text}

Fire 0-3 flags. Follow the format in the system prompt. If nothing is actionable, output nothing."""

    try:
        r = subprocess.run(
            [CLAUDE_CMD, "-p", "--system-prompt", static_context,
             "--model", CLAUDE_MODEL, user_msg],
            capture_output=True, text=True, timeout=CLAUDE_TIMEOUT
        )
        if r.returncode != 0:
            write_log(f"  [Claude error: exit {r.returncode}] {r.stderr[:100]}")
            return []
        return parse_flags(r.stdout)
    except subprocess.TimeoutExpired:
        write_log("  [Claude timeout — skipping this cycle]")
        return []
    except Exception as e:
        write_log(f"  [Claude error] {e}")
        return []


# Flag-line prefixes the model is told to use (see the SKILL.md context template).
FLAG_PREFIX_CHARS = "📋⏱📌🎯🤝📊🔄👤❓⚡🏁📖"

def parse_flags(text):
    """Extract flag lines from Claude's response."""
    flags = []
    for line in text.splitlines():
        line = line.strip()
        if not line or len(line) < 5:
            continue
        if line.startswith("→") or line.startswith("✓") or line[0] in FLAG_PREFIX_CHARS:
            flags.append(line)
    return flags[:3]  # max 3 per cycle


# ── Suppression engine ───────────────────────────────────────────────────────
def extract_role_from_context(static_context):
    """Parse 'My Role:' out of the context file. Defaults to lead/facilitator."""
    for line in static_context.splitlines():
        if "My Role:" in line:
            return line.split("My Role:")[-1].strip().lower()
    return "lead/facilitator"


def extract_flag_type_topic(flag_line):
    """Extract (TYPE, topic) from a flag line for dedup."""
    clean = flag_line.lstrip("→✓" + FLAG_PREFIX_CHARS + " ")
    parts = clean.split("—")
    if len(parts) >= 2:
        return parts[0].strip().upper(), parts[1].strip().lower()
    return clean[:20].upper(), ""


def should_suppress(flag_line, role):
    """Backstop suppression. The richer, per-meeting rules live in the context file;
    this enforces a couple of role-based defaults plus same-topic dedup so an
    occasional model slip doesn't spam the log."""
    ftype, topic = extract_flag_type_topic(flag_line)

    # Role-based backstop (mirror the SKILL.md suppression table).
    if "subordinate" in role or "reportee" in role:
        # Suppress "mobilize the room / you own this" style nudges when you're not leading.
        if "MOBILIZE" in ftype or "OWN" in ftype:
            return True
    if "listener" in role:
        # As a listener, suppress personal coaching; keep tactical + strategic flags.
        coaching_types = ["PROPOSAL", "HEDGE", "OVEREXPLAIN", "HEADLINE", "CLEAR", "PROBE",
                          "MOBILIZE", "ASSERT", "FRAMEWORK"]
        if any(ct in ftype for ct in coaching_types):
            return True

    # Dedup: same type+topic within 5 minutes.
    now = time.time()
    for ts, prev_type, prev_topic, _ in flag_history:
        if now - ts < 300 and prev_type == ftype and prev_topic == topic:
            return True

    return False


# ── Log + notify ─────────────────────────────────────────────────────────────
def write_log(text):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(text + "\n")


def notify(msg):
    """Fire a desktop notification (macOS only). Safe no-op elsewhere / on failure.
    Delete this function and its call sites if you don't want notifications."""
    try:
        clean = msg.encode("ascii", "ignore").decode().strip() or msg[:90]
        subprocess.run(
            ["osascript", "-e",
             f'display notification "{clean[:90]}" with title "Meeting Brain"'],
            capture_output=True, timeout=3
        )
    except Exception:
        pass


def write_startup(transcript_id, skipped_to=None, total=None):
    bar = "━" * 55
    write_log(f"\n{bar}")
    write_log(f"  MEETING BRAIN — LIVE")
    write_log(f"{bar}")
    write_log(f"  Transcript: {transcript_id}")
    write_log(f"  Interval:   {POLL_INTERVAL}s")
    write_log(f"  Model:      {CLAUDE_MODEL}")
    if skipped_to is not None and total is not None:
        write_log(f"  Skipped to: line {skipped_to} of {total}")
    write_log(f"{bar}")
    write_log(f"  Polling every {POLL_INTERVAL}s  |  tail -f {LOG}")
    write_log(f"{bar}\n")


def write_session_summary():
    elapsed = int(time.time() - start_time)
    total_flags = sum(flag_counts.values())
    bar = "━" * 55
    write_log(f"\n{bar}")
    write_log(f"  SESSION SUMMARY")
    write_log(f"{bar}")
    write_log(f"  Duration: {elapsed // 60} min")
    write_log(f"  Flags:    {total_flags} total")
    for ftype, count in sorted(flag_counts.items(), key=lambda x: -x[1]):
        write_log(f"    {ftype}: {count}")
    write_log(f"{bar}")


# ── Graceful shutdown ────────────────────────────────────────────────────────
def handle_shutdown(signum, frame):
    write_session_summary()
    write_log("  MEETING BRAIN — stopped (signal received)")
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)


# ── Main poll loop ───────────────────────────────────────────────────────────
def main():
    global meeting_summary

    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))
    if os.path.exists(STATE_LINES):
        os.remove(STATE_LINES)

    static_context = load_static_context()
    role = extract_role_from_context(static_context)

    open(LOG, "a").close()  # ensure the log exists (append mode, never truncate)

    last_seen     = 0      # number of transcript lines already processed
    empty_polls   = 0
    cycle         = 0
    catchup_mode  = False
    primed_cycles = 0      # how many upcoming live cycles to inject the priming summary

    # ── Optional: wait for the transcript to first appear ──────────────────────
    if WAIT_MODE:
        while not fetch_transcript_lines(TRANSCRIPT_ID):
            write_log(f"  — (waiting for transcript {TRANSCRIPT_ID} to appear)")
            time.sleep(POLL_INTERVAL)

    # ── Skip-to-tail on a mid-meeting launch ──────────────────────────────────
    if not FROM_START:
        lines = fetch_transcript_lines(TRANSCRIPT_ID)
        total = len(lines)
        if total >= SKIP_TO_TAIL_MIN:  # significant backlog already present
            meeting_summary, skip_index = prime_from_tail(lines)
            last_seen = skip_index
            if skip_index > 0:
                primed_cycles = 5  # inject the summary for the first few live cycles
            write_startup(TRANSCRIPT_ID, skipped_to=skip_index, total=total)
        else:
            write_startup(TRANSCRIPT_ID)
    else:
        write_startup(TRANSCRIPT_ID)

    # ── Poll ───────────────────────────────────────────────────────────────────
    while empty_polls < MAX_EMPTY:
        current_interval = CATCHUP_INTERVAL if catchup_mode else POLL_INTERVAL
        time.sleep(current_interval)
        cycle += 1

        lines = fetch_transcript_lines(TRANSCRIPT_ID)

        # Defensive: if the transcript shrank/reset under us, re-baseline.
        if len(lines) < last_seen:
            last_seen = len(lines)

        new_lines = lines[last_seen:]

        if not new_lines:
            if catchup_mode:
                catchup_mode = False
                write_log(f"  [{cycle}] CATCHUP COMPLETE — back to {POLL_INTERVAL}s interval")
            write_log(f"  [{cycle}] — (no new transcript)")
            empty_polls += 1
            continue

        # We have new content.
        last_seen = len(lines)
        empty_polls = 0
        try:
            with open(STATE_LINES, "w") as fh:
                fh.write(str(last_seen))
        except Exception:
            pass

        # ── Backlog fast-forward: a big jump means we're behind → consume, don't analyze
        if len(new_lines) >= CATCHUP_BATCH:
            if not catchup_mode:
                catchup_mode = True
                write_log(f"  [{cycle}] CATCHUP MODE — fast-forwarding at {CATCHUP_INTERVAL}s")
            write_log(f"  [{cycle}] CATCHUP: +{len(new_lines)} lines, consuming...")
            continue
        elif catchup_mode:
            catchup_mode = False
            write_log(f"  [{cycle}] CATCHUP COMPLETE — back to {POLL_INTERVAL}s interval")

        new_text = " ".join(new_lines).strip()
        if not new_text:
            write_log(f"  [{cycle}] — (empty text)")
            empty_polls += 1
            continue

        write_log(f"  [{cycle}] {len(new_text)} chars -> analyzing...")

        # ── Analyze with Claude ────────────────────────────────────────────────
        ctx_summary = meeting_summary if primed_cycles > 0 else ""
        if primed_cycles > 0:
            primed_cycles -= 1

        flags = analyze(new_text, static_context, ctx_summary)

        # Apply suppression + record surviving flags.
        surviving = []
        for flag in flags:
            if not should_suppress(flag, role):
                surviving.append(flag)
                ftype, topic = extract_flag_type_topic(flag)
                flag_history.append((time.time(), ftype, topic, flag))
                flag_counts[ftype] = flag_counts.get(ftype, 0) + 1

        for flag in surviving:
            write_log(f"  {flag}")
            notify(flag)

        if not surviving:
            write_log("  (no flags)")

    # Session ended due to silence.
    write_session_summary()
    write_log(f"  MEETING BRAIN — stopped (no new content for {int(MAX_EMPTY * POLL_INTERVAL / 60)} min)")
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)


if __name__ == "__main__":
    main()
