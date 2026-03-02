# Self-Improving AI Memory via Tana MCP

> Your AI skills get smarter every session. The memory and the improvements live in Tana — portable to every LLM that can connect.

---

## The Real Problem

Most people think the challenge with AI tools is getting good output today. The actual challenge is **keeping the quality tomorrow**.

You build a prompt that works. Next session: forgotten. You correct a failure and the AI gets it right. Next session: same mistake. You spend 30 minutes getting context loaded. Next tool: start from zero.

The problem isn't a single bad session. It's that your AI system **doesn't compound**. Every session you're rebuilding instead of building on.

This project is about changing that.

---

## The Proof It Works

Here's a real example. Over 14 coaching sessions (Oct 2025–Feb 2026), a meeting assessment prompt was iteratively improved:

- **v1.0:** Basic action item extraction, no soft skills assessment
- **v1.1:** Added CARE/ARE/Pyramid framework detection
- **v1.3:** Extended extraction to full meeting notes, not just action items (discovered after missing 10 tasks in one session)
- **v1.8:** Added speaker attribution handling for non-diarized transcripts
- **v2.1:** Added baseline scoring, overexplaining count, hedge count, mobilization gap check

Each improvement was triggered by a real failure. Each one was captured and persisted. By session 14, the system catches patterns that session 1 missed entirely.

**The prompt that drove this lived in Tana as a single node.** Editable from any LLM with Tana MCP. Every version of it is logged. That's the system this project formalizes.

---

## How It Works

```
                    ┌────────────────────────────────────────┐
                    │          Tana (Source of Truth)        │
                    │                                        │
                    │  #AI_Context nodes:                    │
                    │                                        │
                    │  CONTEXT              SKILLS           │
                    │  • About Me           • my-workflow    │
                    │  • Key People         • task-creation  │
                    │  • Priorities         • weekly-review  │
                    │  • Workspace Schema   • ...            │
                    │                                        │
                    │  Each skill: instructions + eval       │
                    │  criteria + change log (v1.0 → v2.3)  │
                    └──────┬──────────────┬──────────────────┘
                           │ Tana MCP     │ Tana MCP
               ┌───────────▼──┐      ┌───▼─────────────────┐
               │  Claude Code │      │ Gemini / Cowork /   │
               │  (CLI)       │      │ Claude Desktop /    │
               │              │      │ Any LLM with MCP    │
               │ /skill-      │      │                     │
               │  improve     │      │ Reads context +     │
               │ captures     │      │ skills directly     │
               │ corrections  │      │ from Tana at        │
               │              │      │ session start       │
               └──────┬───────┘      └─────────────────────┘
                      │ /ai-memory-sync push
                      │ writes to ALL configured tool paths:
                      ├── ~/.claude/skills/[name]/SKILL.md
                      ├── ~/.gemini/prompts/[name].md
                      ├── ~/.ai-skills/[name]/skill.md
                      │
                      │ /ai-memory-sync export
                      ▼
               ┌──────────────┐
               │ Claude Mobile│
               │ (flat .md    │
               │  for Projects│
               └──────────────┘
```

**Skills in Tana are tool-agnostic.** The node stores instructions in plain language. `/ai-memory-sync` translates them into each tool's format when writing local files — `SKILL.md` for Claude Code, plain `.md` for Gemini, JSON for tools that need it. You configure which tools you use once (in `manifest.skillPaths`), and every improvement propagates to all of them automatically.

**Context loading is deterministic.** After setup, every LLM interface loads context via `read_node` with hardcoded node IDs — not search queries. This guarantees your behavioral rules and context are always loaded correctly regardless of how different LLM interfaces handle MCP parameters.

The `Modified By` field (`claude-code`, `other-llm`, `manual`) enables conflict-free sync. Any LLM that updates a node signals the change — the sync skill picks it up on the next run.

**Note on local MCP:** Tana MCP currently runs as a local server, so direct node access works for apps on the same machine (Claude Code CLI, Claude Desktop, Cowork, Gemini CLI). For remote access — Claude mobile, any web-based tool — use `/ai-memory-sync export` to generate a flat markdown file you can upload to a Claude Project.

**Tana Voice:** `#AI_Context` nodes double as natural starting points for Tana Voice conversations. Long-press any node to begin a voice session with that context already loaded — your development areas node for a coaching reflection, your org context node for a business discussion, your priorities node for a weekly planning conversation. No extra setup required.

---

## The Three Skills

### `/ai-memory-setup` — Bootstrap

Run once. The skill:
1. Reads your Tana knowledge graph — meeting tags, task structures, recurring people, active themes
2. Asks 3 targeted questions based on what it found
3. Creates the `#AI_Context` framework in Tana: 5 context nodes + skill nodes for every skill in `~/.claude/skills/`
4. Writes a sync manifest mapping Tana nodes to local files
5. Generates Cowork/Claude Desktop folder instructions with your real field IDs filled in

Every skill gets a Tana node with: its current instructions, inferred eval criteria, and a change log initialized at v1.0.

### `/ai-memory-sync` — Stay Current

Run after sessions where things changed:
- `check` — see what's stale and in which direction
- `pull` — pull changes made by other LLMs from Tana
- `push` — push local updates to Tana (auto-increments version)
- `enrich` — scan recent meetings/tasks, suggest context + skill updates
- `export` — generate flat markdown for mobile / Claude Projects

### `/skill-improve` — The Improvement Loop

This is the core of the self-improving system.

**Auto-triggers after corrections.** When a skill runs and produces wrong output, and the user corrects it, Claude Code offers:

> "Should I save this as a permanent improvement to [skill-name]? It'll prevent the same issue in future sessions."

On confirmation:
- Reads the current skill from Tana
- Generates a surgical diff (only the broken section)
- Shows before/after for user confirmation
- Updates local SKILL.md + Tana node
- Increments version (v1.2 → v1.3)
- Appends to Change Log with the failure that triggered it

Over time, the Change Log becomes a record of every time the skill got smarter:

```
Change Log — tana-action-items
v2.1 (2026-03-01) — Fixed attribution: read explicit ownership before
                    defaulting. Triggered by: wrong assignee in 1:1.
v2.0 (2026-02-27) — Extended soft skills check to 21 development areas.
                    Triggered by: missed overexplaining pattern in baseline.
v1.3 (2026-02-11) — Extended extraction to full meeting notes.
                    Triggered by: missed 10 tasks in planning meeting.
v1.0 (2026-02-06) — Initial version.
```

---

## Install

### Prerequisites
- Claude Code CLI (`claude` command)
- Tana with local API / MCP server running (see [tana.inc/docs/local-api-mcp](https://tana.inc/docs/local-api-mcp))
- MCP connected in Claude Code (`/mcp` shows "Connected to tana")

### Step 1: Install the skills

```bash
mkdir -p ~/.claude/skills
cp -r skills/ai-memory-setup ~/.claude/skills/
cp -r skills/ai-memory-sync ~/.claude/skills/
cp -r skills/skill-improve ~/.claude/skills/
```

### Step 2: Run setup

```
claude
> /ai-memory-setup
```

Takes 3–5 minutes. Reads your workspace, asks 3 questions, creates everything in Tana.

### Step 3: Connect any other LLM (optional)

Paste `~/.claude/ai-memory/llm-session-instructions.md` into your LLM's folder or project instructions. Works with Claude Desktop, Gemini, Cowork, or any tool with Tana MCP. Every conversation auto-loads your context from Tana.

### Step 4: Mobile (optional)

```
> /ai-memory-sync export
```

Upload `~/.claude/ai-memory/ai-context-export.md` to a Claude Project.

---

## The #AI_Context Schema

One supertag, two types of nodes:

| Field | Type | Purpose |
|-------|------|---------|
| Context Type | Options | `behavioral`, `schema`, `memory`, `reference`, **`skill`** |
| Priority Tier | Options | `tier-1-critical`, `tier-2-important`, `tier-3-reference` |
| Version | Plain text | `v1.3` — increments on every improvement |
| Last Synced | Date | When this node was last updated |
| Modified By | Options | `claude-code`, `other-llm`, `manual` |
| Local File Path | URL | Path to local file (for CLI sync) |

**Context nodes** (tier-1): loaded every session. Who you are, your priorities, your relationships, your workspace schema, your rules.

**Skill nodes** (tier-2): loaded on demand. Full instructions + eval criteria + change log. Any LLM reading the node gets the latest version of the skill.

---

## Files

```
skills/
  ai-memory-setup/SKILL.md    — Bootstrap skill
  ai-memory-sync/SKILL.md     — Sync skill
  skill-improve/SKILL.md      — Improvement capture skill
README.md                     — This file
SETUP.md                      — Detailed walkthrough
llm-session-instructions.md   — Template for any LLM with Tana MCP (Claude Desktop, Gemini, etc.)
```
