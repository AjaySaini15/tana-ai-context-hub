---
name: meeting-brain
description: Real-time meeting co-pilot for Tana + Claude. Polls a Tana transcript node and, every interval, sends the newest transcript chunk to Claude (via `claude -p` with a cached system-prompt context file) and emits 0–3 short, actionable flags — coaching cues (over-explaining, hedging, etc.), meeting-management nudges (agenda, decisions, action items), and strategic prompts. Auto-skips to the live edge when launched mid-meeting. Use when the user says "start meeting brain", "launch meeting assistant", "start brain for [meeting]", "/meeting-brain", or "stop meeting brain".
argument-hint: "[meeting name or transcript node ID, e.g. 'Q3 Roadmap Sync', 'demoTrnsQ3001', '--interval 30']"
---

# Skill: Meeting Brain — Real-Time Meeting Co-Pilot

A live polling loop that turns a Tana transcript into a real-time meeting assistant. While a
meeting is being transcribed into Tana, this skill repeatedly reads the new transcript text and
asks Claude to fire short flags: gentle coaching cues, meeting-management nudges, and strategic
prompts drawn from whatever prep you loaded.

> **Why Tana makes this possible.** Tana's local API exposes the **in-progress** meeting transcript as
> queryable nodes — so you can *poll it mid-meeting*. Most transcription tools only hand you the
> transcript *after* the meeting ends; Tana lets you ping the live transcript every few seconds, which
> is exactly what turns a note-taker into a real-time co-pilot. This whole skill is built on that one
> capability. Paired with the included **Coach overlay** (`coach-popup.swift`, Step 7), the flags land
> in a floating panel on your screen *while you're still in the room*.

> Examples in this skill use the fictional workspace from
> [`demo-workspace/DEMO-WORKSPACE.md`](../../demo-workspace/DEMO-WORKSPACE.md). All node IDs shown
> (e.g. the meeting `demoMtgQ3Road` and its transcript `demoTrnsQ3001`) are placeholders — swap
> them for your own. See [`GETTING-STARTED.md`](../../GETTING-STARTED.md) → "Finding your own IDs".

> **Just want to see it run?** [`demo/`](demo/) replays a captured sample session into the overlay —
> no Tana wiring needed: `cd demo && python3 replay-coach-log.py` (≈60s, then watch the ⚡ panel).

**Engine:** `claude -p --system-prompt` — uses your existing Claude Code auth, no API key or SDK
needed. The model is configurable (see the constants block in `meeting-brain.py`).
**Token efficiency:** Claude auto-caches repeated system prompts above ~1024 tokens, so the static
context file is sent every cycle but cached server-side — only the new transcript chunk is fresh
input each call.
**Language:** Claude reads multilingual transcripts natively. If your meetings are not in English,
tell the context file to read the source language but always emit flags in English (or your
preferred output language). See the optional "Output language" note in Step 4.

---

## How it works (the method)

```
        ┌─────────────────────────────────────────────────────────────┐
        │  SKILL.md (this file) — orchestration, run ONCE at start      │
        │   1. resolve meeting → transcript node                        │
        │   2. gather prep/context → write  ./meeting-brain-context.md   │
        │   3. launch meeting-brain.py in the background                 │
        └─────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
        ┌─────────────────────────────────────────────────────────────┐
        │  meeting-brain.py — the polling loop, runs continuously        │
        │   • every N s: fetch transcript lines for the node             │
        │   • diff against what it has already seen → new chunk           │
        │   • send new chunk + recent-flags + context file to `claude -p` │
        │   • parse 0–3 flag lines → write to the log / notify            │
        │   • skip-to-tail if launched mid-meeting (big backlog)          │
        │   • backlog fast-forward: poll fast & consume until caught up   │
        └─────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
      ⚡ coach-popup.swift overlay   —or—   tail -f /tmp/meeting-brain.log
```

The taxonomy of *what* to flag is **not hard-coded in the script** — it lives entirely in the
context file this skill writes (Step 4). That keeps the engine generic and lets you re-tune the
coaching/strategy emphasis per meeting without touching code.

---

## Trigger phrases

- "start meeting brain" / "launch meeting assistant" / "start the co-pilot"
- "start brain for [meeting name]"
- "/meeting-brain [meeting name] [--interval N]"
- "stop meeting brain" / "kill meeting brain" / "stop the brain"
- "meeting brain status" / "check the brain"

---

## Prerequisites (one-time)

1. **Implement the transcript reader.** `meeting-brain.py` ships with a clearly-marked stub,
   `fetch_transcript_lines(node_id) -> list[str]`. You must wire it to *your* Tana before the loop
   does anything useful — see "What you must implement" at the bottom of this file and the comment
   block in the script.
2. **Confirm `claude -p` works** from your shell (`claude -p "hello"` should return text). The
   script shells out to it; no API key is needed if Claude Code is already authenticated.
3. **Pick a viewer.** The script appends flags to a plain log file. On macOS, build the included
   `coach-popup.swift` overlay (a floating menu-bar panel — see Step 7) for a glanceable live co-pilot;
   on any OS, `tail -f /tmp/meeting-brain.log` works too.

---

## START — Input modes

Accept whatever the user provides; resolve the rest from Tana.

### Mode A — Meeting name only
> "start meeting brain for Q3 Roadmap Sync"

→ search Tana for the meeting node → find its transcript child → load context.

### Mode B — Meeting node ID
> "start meeting brain, meeting node demoMtgQ3Road"

→ use the node → find its transcript child → load context.

### Mode C — Transcript ID given directly
> "start brain, transcript demoTrnsQ3001"

→ use it directly, skip discovery.

### Interval override
Append `--interval 30` (or any number of seconds) to any mode. Default: 60s.

---

## Step 1: Resolve the meeting node

If a meeting **name** was given but no node ID, search Tana for it. Using the Tana MCP server:

```
search_nodes({ "and": [ {"hasType": "<your-#Meeting-tag-id>"},
                         {"textContains": "<meeting name>"} ] })
```

(In the demo workspace the `#Meeting` tag is `demoMeetTag1`; a search for "Q3 Roadmap Sync" resolves
to `demoMtgQ3Road`.) Pick the most recent match. If ambiguous, show the top 2 and ask.

If the user already gave a transcript node ID (Mode C), skip this step.

---

## Step 2: Find the transcript node

If the transcript ID was not provided, read the meeting node's children and look for the one holding
the transcript (in the demo schema that's the **Transcript** field, `demoFldTrns1`, whose value node
is `demoTrnsQ3001`):

```
get_children(<meeting-node-id>)        # then pick the "Transcript" child
```

**If found** → use that node ID as `--transcript`.
**If not found yet** (meeting hasn't started transcribing) → tell the user, and pass `--wait` so the
script polls until content appears.
**Fallback** → ask the user to paste the transcript node's link/ID from Tana if auto-discovery fails
after a couple of tries.

---

## Step 3: Gather context

This is where the value comes from. Collect whatever prep you have for this meeting; it all gets
written into the single context file in Step 4. None of this is required — with an empty context
file the brain still fires generic coaching/management flags — but the richer the context, the
sharper the strategic flags.

Pull whatever of the following exists in *your* system:

- **Agenda / prep notes** — if you (or another skill) already compiled a meeting brief, use it as the
  primary context and skip the rest of this step. A good brief typically contains: the agenda, open
  action items to push, stakeholder notes, any relevant metrics, and a focus for the meeting.
- **Open action items** — unchecked tasks linked to this meeting or its recurring series, which become
  "push points" the brain reminds you to raise.
- **Attendees + their roles** — from the meeting node's Attendees field (in the demo schema,
  `demoFldAtnd1`). Knowing who is in the room lets the brain tailor what it watches for.
- **Your role in the meeting** — are you leading, a peer, a subordinate/reportee, or just listening?
  In the demo schema this is the **My Role** field (`demoFldRole1`: Lead / Peer / Subordinate /
  Listener). It drives the suppression rules below. If unset, infer it from the attendees (most senior
  person in the room relative to you).
- **Stakeholder history** — if you keep `#PersonObservation`-style notes (demo: `demoObsTag01`) on the
  attendees, summarize the relevant ones so the brain can surface "this person tends to…" intel.
- **Any manual focus** the user gave in the invocation (e.g. "today, watch my tendency to over-explain"
  or "push the pricing decision").

### Suppression rules (derived from your role)

Use the role to decide which flag lanes are active. Suggested defaults:

| Your role | Coaching flags | Meeting-management flags | Strategic flags |
|-----------|----------------|--------------------------|-----------------|
| **Lead / Facilitator** | active | active | active |
| **Peer** | active | active | active |
| **Subordinate / Reportee** | active (focus on assertiveness/clarity) | active | active; *suppress* "you own this / mobilize the room" prompts |
| **Listener** | suppressed | tactical only (agenda, decisions, action items) | active |

Write the chosen suppressions into the context file so the model honors them, and pass the role to the
script (it parses `My Role:` from the context file and also enforces a couple of these rules as a
backstop — see `should_suppress` in `meeting-brain.py`).

---

## Step 3.5: Infer the meeting type (optional but useful)

Classifying the meeting lets you tell the model which flag types to emphasize. Infer from the title and
attendees. These are illustrative buckets — adapt to your own meeting mix:

| Type | Signal | Emphasize | De-emphasize |
|------|--------|-----------|--------------|
| **Brainstorming** | title says "brainstorm / ideation / strategy session" | reframes, generative questions, "good moment" callouts | strict agenda tracking |
| **Review / accountability** | "review / weekly / pipeline", a group of your reports | decision-locking, action capture, probing vague answers | reframes |
| **1:1** | exactly one other attendee who reports to you | developmental questions, acknowledgement, person intel | agenda tracking |
| **Upward / senior** | your manager or an executive is present | recall the right data, confidence cues, drop hedging | "mobilize the room" (suppressed) |
| **Cross-functional** | several peers from other functions | reframes, presence/impression, timing cues | heavy personal coaching |
| **Townhall / presentation** | "all-hands / townhall", large audience | narrative/clarity coaching, drop over-explaining | accountability probing |

Write the inferred type and its emphasis into the context file.

---

## Step 4: Write the static context file

Assemble everything from Step 3 (+3.5) into the context file the script reads. **Path:**
`./meeting-brain-context.md` by default (configurable — see `CONTEXT_FILE` in `meeting-brain.py`; many
users point it at a temp path like `/tmp/meeting-brain-context.md`). Use this template — fill the
sections you have, delete the ones you don't:

```markdown
# Meeting Brain — System Context

## Identity
You are a real-time meeting co-pilot. As the meeting is transcribed, you receive the newest chunk of
transcript every [INTERVAL]s. Fire 0-3 short, actionable flags per chunk — coaching cues, meeting-
management nudges, and strategic prompts. Be terse. If nothing is worth flagging, output nothing.
(Output language: English. If the transcript is in another language, read it natively but write flags
in English / Roman script.)

## This Meeting
- Name: [meeting name]
- Type: [Review / 1:1 / Upward / Cross-functional / Townhall / Brainstorming]
- My Role: [Lead/Facilitator | Peer | Subordinate/Reportee | Listener]
- Attendees: [name (role), name (role), ...]

## Prep / Strategy
[Paste your compiled agenda + brief here if you have one — it is the primary context.
Include open action items to push, stakeholder notes, relevant metrics, and the focus for today.]

## Push Points (remind me to raise these)
[Open action items / topics to bring up — the brain fires a PUSH flag when the conversation is on-topic.]

## Coaching Watch List (generic categories — tune to your own habits)
WATCH: Over-explaining (a point dragging past ~3 sentences), Hedging ("I think / maybe / kind of"),
Not asking for the other person's proposal before giving your own, Burying the headline under context.
[Add or remove categories to match what you personally want to work on.]

## Suppression Rules
- "Mobilize the room" / ownership prompts: [ACTIVE / SUPPRESSED]
- Acknowledgement prompts: [ACTIVE / SUPPRESSED]
- All coaching flags: [ACTIVE / SUPPRESSED]

## Flag Format
One line per flag. Max 3 per chunk. Each line must start with one of the prefixes below so the script
can pick it up. Keep `[topic]` to a concrete 2–5 word phrase or a person's name — never "this point".

### Coaching (about how I am speaking — assume unattributed speech is mine)
→ PROPOSAL — [topic] — ask for their proposal first: "What's your suggestion?"
→ HEDGE — [topic] — drop the hedge. State it: "[confident rewrite]"
→ OVEREXPLAIN — [topic] — point made. Move on.
→ HEADLINE — [topic] — lead with the takeaway, then the context.
→ PROBE — [person] is dodging [topic]. Ask: "[specific question]"
✓ CLEAR — [topic] — clean, confident statement (positive reinforcement).

### Meeting management (about the conversation)
📋 AGENDA — [uncovered item] — [time context, e.g. "20 min in, 3 items left"]
⏱ TIME — [current topic] running long — [items remaining]
📌 ACTION — [person] to [task] by [date]
🎯 PUSH — Open: [push-point item]. Raise it now — the conversation is on this topic.
📊 DECISION — Lock it: who owns [X], by when? Don't let it drift.

### Strategic (about the bigger picture, using your prep)
📖 RECALL — [topic] — from prep, cite: [specific data point]
👤 INTEL — [person] tends to [pattern from your notes] — [how to handle]
⚡ TIMING — [speak now / hold / lock the decision] — [why this moment matters]
❓ QUESTION — ask: "[specific, depth-revealing question]"
🔄 REFRAME — "[negative framing heard]" → reframe to: "[action-oriented version]"
🤝 MOMENT — [person] [win / frustration / effort] — acknowledge: "[short phrase]"

## Priority Order
1. ⚡ TIMING (time-sensitive)
2. 📖 RECALL, 👤 INTEL (surface prep when the relevant topic is live)
3. Meeting management (AGENDA, ACTION, DECISION, PUSH)
4. Coaching (HEDGE, OVEREXPLAIN, PROPOSAL, HEADLINE)
5. Strategic (QUESTION, REFRAME, MOMENT)
Never fire more than 1 coaching flag + 2 other flags per chunk.

## Output Rules
- [topic] always concrete (a name or a 2-5 word phrase). NEVER "this point".
- If nothing actionable in this chunk → output NOTHING (empty response).
- Don't repeat a flag type+topic you already fired (you'll see LAST 5 FLAGS in the user message).
- RECALL / INTEL: only fire while the transcript is actively on that topic. Don't volunteer unprompted.
- QUESTION: make it specific and strategic, not generic.
- TIMING: only for genuine moments, not every time someone speaks.
```

> **Why a file, not inline?** The script sends this file verbatim as the `--system-prompt` on every
> cycle. Claude caches it, so re-sending costs little, and you can edit emphasis mid-meeting by editing
> the file (the script re-reads it only at start, so for live edits, stop and restart).

---

## Step 5: Clear stale state from any previous run

```bash
pkill -f meeting-brain.py 2>/dev/null
rm -f /tmp/meeting-brain.log /tmp/mb_last_total.txt /tmp/mb_last_len.txt
echo "cleared"
```

---

## Step 6: Start the polling script

Build the command from the resolved values. Adjust the path to wherever you keep the script.

```bash
nohup python3 ./scripts/meeting-brain.py \
  --transcript <transcript-node-id> \
  [--meeting-node <meeting-node-id>] \
  --interval <interval> \
  [--wait] \
  [--from-start] \
  > /tmp/meeting-brain-stdout.log 2>&1 &
echo $! > /tmp/meeting-brain.pid
echo "PID: $(cat /tmp/meeting-brain.pid)"
```

- `--transcript` (required) — the transcript node ID from Step 2 (e.g. `demoTrnsQ3001`).
- `--meeting-node` (optional) — the meeting node, used only for richer chunk discovery if you wire it up.
- `--from-start` — disables skip-to-tail; only use when you explicitly want to process the whole
  transcript from the beginning. Default behavior auto-detects a large transcript and skips to the live
  edge so a mid-meeting launch doesn't churn through stale history.
- `--wait` — keep polling until transcript content appears (use when the meeting hasn't started yet).

Then confirm startup by reading the log:

```bash
sleep 5 && tail -20 /tmp/meeting-brain.log
```

---

## Step 7: Point a viewer at the log

The script appends every flag to `LOG` (default `/tmp/meeting-brain.log`). Two ways to watch it:

**Recommended (macOS) — the Coach overlay.** This repo ships [`coach-popup.swift`](coach-popup.swift),
a tiny menu-bar app (⚡) that floats an always-on-top panel in the corner of your screen and shows the
latest flags live, color-coded (orange = nudge `→`, green = positive `✓`, grey = session header). It
pulses the menu-bar icon on a new flag, so you get a glanceable co-pilot without staring at a terminal.
Build and run it once (from `skills/meeting-brain/`):

```bash
swiftc -O coach-popup.swift -o Coach && ./Coach     # or, no build step:  swift coach-popup.swift &
```

It reads the same log (`$MEETING_BRAIN_LOG`, default `/tmp/meeting-brain.log`), so just leave it running
across meetings — it auto-clears when a new session truncates the log. Close the panel to hide it (the
app keeps running in the menu bar); "Quit Coach" from the ⚡ menu to stop it.

**Cross-platform fallback — tail the log.** Any OS, nothing to build:

```bash
tail -f /tmp/meeting-brain.log
```

(On macOS the script also fires a desktop notification per flag via `osascript`; remove that call in
the script if you don't want notifications or aren't on macOS.)

---

## Step 8: Confirm to the user

```
Meeting Brain running.
  Meeting:    <name>
  Type:       <inferred meeting type>
  Transcript: <transcript-node-id>
  PID:        <pid>
  Interval:   <N>s
  Context:    <"from compiled prep" or "minimal (no prep)">
  Role:       <Lead / Peer / Subordinate / Listener>
  Suppressions: <any active suppressions>
  [Skipped to: node N of M  (only if a mid-meeting launch triggered skip-to-tail)]

Watching: tail -f /tmp/meeting-brain.log
To stop: "stop meeting brain"
```

---

## STOP

When the user says "stop meeting brain" / "kill meeting brain":

```bash
pkill -f meeting-brain.py && echo "Stopped" || echo "No process running"
```

After stopping, optionally summarize the session: read `/tmp/meeting-brain.log`, count flags by type,
and note the few most useful coaching/strategic moments. If you keep a daily note or meeting summary in
Tana, append that recap there (read first, then append — never overwrite).

---

## STATUS

```bash
pgrep -f meeting-brain.py && echo "RUNNING (PID: $(pgrep -f meeting-brain.py))" || echo "NOT RUNNING"
tail -20 /tmp/meeting-brain.log
```

---

## What you must implement

This skill is fully runnable **once you do two things**:

1. **Fill the transcript-reader stub.** Open `meeting-brain.py` and implement
   `fetch_transcript_lines(node_id) -> list[str]` so it returns the transcript's lines, in order, as
   plain strings — newest at the end. The script handles all the diffing, chunking, and skip-to-tail
   on top of whatever this returns. Three common ways to back it (pick one — see the comment block in
   the script):
   - **Tana local desktop server** — if you run the Tana desktop app, it can host a local HTTP
     endpoint you query for a node's children.
   - **An MCP bridge** — call your Tana MCP server's `get_children` on the transcript node and return
     each child's text. (This repo's other skills use that MCP server: `mcp__tana-local__get_children`.)
   - **An exported / synced transcript file** — if your transcript is mirrored to a local file, just
     read and split it. Easiest way to test the loop end-to-end.

2. **Set the config constants** at the top of `meeting-brain.py` if the defaults don't suit you:
   `CLAUDE_CMD` (how to invoke Claude, default `claude`), `CLAUDE_MODEL` (default `sonnet`),
   `CONTEXT_FILE` (default `./meeting-brain-context.md`), and the log/state paths.

Everything else — the polling loop, chunk diffing, the `claude -p` call with the cached context file,
skip-to-tail on mid-meeting launch, backlog fast-forward, flag parsing, suppression, and the session
summary — already works around that stub.

---

## Notes & tuning

- **Engine:** Claude via `claude -p --system-prompt` — no API key/SDK; uses your Claude Code auth.
- **Default interval:** 60s (`--interval N` to change). Stops after ~20 min with no new content.
- **Mid-meeting launch:** if the transcript already has many nodes, the script reads the tail, asks
  Claude for a short "meeting so far" summary, and starts live from the edge — so you don't get a flood
  of flags about already-finished discussion.
- **Backlog fast-forward:** if it falls behind (a full batch keeps coming), it polls fast and just
  *consumes* transcript without analyzing until it catches up, then resumes the normal interval.
- **Context file is the brain's brain.** All coaching/strategy emphasis lives there (Step 4), not in
  the code — re-tune per meeting by editing the template you write.
