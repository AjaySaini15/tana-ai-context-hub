# Getting Started — Operating Your Tana with Claude

[SETUP.md](SETUP.md) gets your **memory hub** running (the `#AI_Context` nodes + the self-improving loop). This guide is the next step: the four **operating skills** that actually *do work* against your Tana graph — and how to point them at your own workspace.

It's written for someone **new to Tana, or returning after a gap** — maybe coming from OneNote, Notion, Roam, or Obsidian — who wants an LLM wired into their notes, not just a chat window next to them.

---

## The one mental shift

If you're coming from a notebook tool (OneNote, Evernote, Notion docs), the instinct is to port your *pages* over. Don't. The reason a graph tool earns its keep is that real knowledge work isn't pages — it's **entities that link**: people, meetings, tasks, decisions, problems, projects. A task has an assignee (a person) and a context (a project); a meeting produces decisions and observations about people; a problem accumulates decisions over time.

```
        Tana = the memory/graph layer  ←→  Claude = the intelligence layer
        (stores entities + links)           (reads the graph, does the work)
```

You don't model all of that on day one. You start with **one supertag** (usually `#Task` or `#Meeting`), let the skills below work it, and grow the schema as you feel the need. That iterative path — start small, add fields/tags as real work demands them — is the whole point of a graph that evolves.

> **Guard against over-engineering.** It's tempting to add a feedback tweak every session until the system is brittle. Layer capability deliberately (capture tasks → then person notes → then live coaching), and keep an eye on complexity and token cost.

---

## Prerequisites

- **Claude Code CLI** — `claude` works in your terminal
- **Tana** with the local API / MCP server running — see [tana.inc/docs/local-api-mcp](https://tana.inc/docs/local-api-mcp)
- MCP connected (`/mcp` in Claude Code shows "Connected to tana")
- The skills installed (see [README → Install](README.md#install))

If you haven't set up the memory hub yet, do [SETUP.md](SETUP.md) first — it's what makes Claude load *your* context at session start.

---

## Read this first: the demo workspace

Every skill here is written as a worked example against one fictional workspace — three collaborators (Riya, Tom, Maya), three contexts (Product, Sales, Hiring), and a `#Task` / `#Meeting` / `#Person` / `#Decision` schema. It's all in **[demo-workspace/DEMO-WORKSPACE.md](demo-workspace/DEMO-WORKSPACE.md)**.

Read it once. Then, everywhere a skill shows an ID like `demoTaskTag1` or `demoRiya0001`, you'll know it's a placeholder you swap for your own (see [Finding your own IDs](#finding-your-own-ids) below).

---

## The four skills — a guided tour

Run them in this order the first time. Each builds the muscle for the next.

### 1. `/tana-understand` — see what you've got
Point it at your workspace and it maps your supertags, fields, and how things link — then suggests where an LLM can help. If you inherited a graph or haven't touched Tana in months, start here. *Output:* a plain-language map of your system + a shortlist of high-value automations.

### 2. `/tana-schema-graph` — picture your schema
Generates a self-contained interactive HTML graph of your supertags and their field relationships. Open it in a browser. This is the fastest way to *see* (not imagine) how your `#Task`, `#Meeting`, and `#Person` tags connect — and to spot a field you should add. Try it on the demo schema first, then your own.

### 3. `/tana-action-items` — turn a meeting into action
The workhorse of the second brain. Give it a meeting summary; it produces structured `#Task` nodes (assignee, context, urgency, a link back to the parent meeting), plus person observations and decisions — deduped against what's already in Tana, behind a single approval gate. This is "capture everything worth retaining," automated. Walk the demo's "Q3 Roadmap Sync" scenario in DEMO-WORKSPACE.md to see the full input→output.

### 4. `/meeting-brain` — a co-pilot during the meeting
Polls a *live* transcript and fires short flags every ~45s via `claude -p` — coaching nudges ("you're explaining, ask a question") and strategic prompts — from a per-meeting context file you generate up front. It ships as a runnable script with **one stub to fill** (see below) — plus the **`coach-popup.swift`** menu-bar overlay so the flags float on your screen mid-meeting. This is the piece that's **unique to Tana**: its local API lets you query the transcript *while the meeting is happening*, not just after it ends.

---

## The Tana bridge — how skills read & write your graph

The skills need a way to read nodes and write nodes. Two paths:

**A. Tana MCP (recommended, zero extra code).** With Tana's local MCP connected, Claude Code calls the `mcp__tana-local__*` tools directly — `search_nodes`, `get_tag_schema`, `read_node`, `get_children`, `import_tana_paste`, `set_field_content`. Most skills in this repo assume this path. Nothing to install beyond the MCP connection from SETUP.md.

**B. A local bridge script (optional).** If you'd rather script against Tana's local HTTP API (e.g. for batch jobs or lower token overhead), wrap it in a small CLI — the skills refer to a `scripts/tana_query.py`-style helper as a placeholder. This repo doesn't ship one (it's setup-specific); the MCP path above covers everything the skills need out of the box.

**The meeting-brain stub.** `skills/meeting-brain/meeting-brain.py` keeps all the polling / chunking / `claude -p` logic intact but leaves **one function for you to implement**:

```python
def fetch_transcript_lines(node_id) -> list[str]:
    # Return the transcript's lines, oldest-first.
    # Back it with: Tana's local server, an MCP get_children call,
    # or an exported transcript file (easiest for a first test).
    ...
```

Fill that, set the config constants at the top (`CLAUDE_CMD`, `CLAUDE_MODEL`, `CONTEXT_FILE`), and it runs. Watch flags with `tail -f /tmp/meeting-brain.log`.

---

## Finding your own IDs

The worked examples use `demo…` IDs. To use a skill on your own graph, swap them for your real node/field IDs. The fastest ways to get them:

- Run **`/tana-schema-graph`** — the graph nodes carry the real IDs.
- Ask Claude (with Tana MCP): *"list my supertags"* then *"show the schema for my Task tag"* — it returns each field's ID.
- In Tana, the node URL (`tana.inc?nodeid=XXXX`) contains the ID.

Drop those into the skill's tana-paste templates in place of the `demo…` placeholders. You only do this once per tag/field.

---

## Coming from OneNote / Notion / Roam?

- **Don't migrate pages — pick one entity.** Make `#Task` or `#Meeting` real first. Let `/tana-action-items` populate it from your next meeting. Momentum beats a perfect schema.
- **Your old notes are an archive, not the system.** Keep them where they are; the graph starts fresh with live work and compounds from there.
- **The summary prompt is yours to shape.** `skills/tana-action-items/references/meeting-summary-prompt.md` is a generic starting prompt — edit it to your meeting types and vocabulary. (Storing that prompt as a single Tana node, editable from any LLM, is exactly the pattern in the [main README](README.md).)

---

## Where to go next

- Wire the memory hub if you haven't: **[SETUP.md](SETUP.md)**
- Understand the self-improving loop: **[README → How It Works](README.md)**
- Improve a skill after it gets something wrong: **`/skill-improve`** (captures the fix permanently)
