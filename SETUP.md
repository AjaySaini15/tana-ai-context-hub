# Setup Guide: Tana as Self-Updating AI Memory

Step-by-step walkthrough for setting up the AI Context Hub in your Tana workspace.

---

## What You'll End Up With

After setup, you'll have:

**In Tana:**
- A new `#AI_Context` supertag with 5 fields
- An "AI Context Hub" node in your Library
- 5 tier-1 context nodes populated from your knowledge graph + your answers

**Locally:**
- `~/.claude/ai-memory/sync-manifest.json` — maps Tana nodes to local files
- `~/.claude/ai-memory/about-me.md` — your role, goals, key relationships
- `~/.claude/ai-memory/workspace-schema.md` — your Tana tag/field structure
- `~/.claude/ai-memory/key-people.md` — key relationships with context
- `~/.claude/ai-memory/active-priorities.md` — current projects and priorities
- `~/.claude/ai-memory/behavioral-rules.md` — rules for your AI to follow
- `~/.claude/ai-memory/llm-session-instructions.md` — ready to paste into any LLM with Tana MCP

---

## Prerequisites

- **Claude Code CLI** installed (`claude` command works in terminal)
- **Tana** with the local API / MCP server running and configured
  - See: https://tana.inc/docs/local-api-mcp
- MCP connected in Claude Code (check with `/mcp` command — should show "Connected to tana")

---

## Step 1: Install the Skills

Download or clone this repository. Then copy the skill folders:

```bash
mkdir -p ~/.claude/skills
cp -r skills/ai-memory-setup ~/.claude/skills/
cp -r skills/ai-memory-sync ~/.claude/skills/
```

Verify they're in place:
```bash
ls ~/.claude/skills/
# Should show: ai-memory-setup  ai-memory-sync
```

---

## Step 2: Run the Setup Skill

Open Claude Code in your terminal:

```bash
claude
```

Then run:

```
/ai-memory-setup
```

### What happens next:

**Phase 1 — Discovery (automatic, ~30 seconds):**

Claude reads your workspace silently:
- Lists all your supertags
- Gets the schema for your meeting, task, person, and project tags
- Samples your 10 most recent meetings
- Finds your most frequently appearing people
- Identifies recurring themes across your meetings and tasks

**Phase 2 — Interview (3 questions, ~2 minutes):**

Claude shows you what it found and asks 3 targeted questions:

> *"I found [N] meeting types, [N] people, and these recurring themes: [X], [Y]. Three quick questions:"*
>
> **Q1:** "In one or two sentences — what's your role and most important goal right now?"
>
> **Q2:** "Of the people I found ([A, B, C...]), who are the 3–5 relationships that matter most for your work?"
>
> **Q3:** "What's one rule you want your AI to always follow?"

Answer these in plain text. Claude uses your answers + the discovery data to populate your context nodes.

**Phase 3 — Build (automatic, ~1 minute):**

Claude creates:
1. The `#AI_Context` supertag in Tana (or uses an existing one)
2. An "AI Context Hub" container in your Library
3. 5 tier-1 context nodes, populated with real data from your graph + your answers
4. Local files mirroring each node
5. The sync manifest

**Phase 4 — Report:**

Claude prints a summary of everything created and next steps.

---

## Step 3: Verify in Tana

Open Tana and navigate to your Library. You should see "AI Context Hub" with 5 child nodes tagged `#AI_Context`.

Open each node to verify the content looks right. If anything needs adjustment, you can:
- Edit directly in Tana (the `Modified By` field will automatically be set to `manual`)
- Or tell Claude Code what to change and it will push the update

---

## Step 4: Connect Any Other LLM (Optional)

After setup, Claude Code generates a ready-to-paste instruction block at `~/.claude/ai-memory/llm-session-instructions.md`.

To use it:
1. Open any LLM that has Tana MCP connected — Claude Desktop, Gemini, Cowork, or others
2. Go to your folder or project settings
3. Paste the contents of `llm-session-instructions.md` as the folder instructions

From that point, every new conversation in that folder will auto-load your Tana context at session start (7 MCP calls: 1 search + 6 reads).

---

## Step 5: Mobile Access (Optional)

For Claude on mobile (iPhone, etc.) or any environment without Tana MCP:

```
/ai-memory-sync export
```

This exports all tier-1 nodes to a single markdown file at `~/.claude/ai-memory/ai-context-export.md`.

Upload this file to a Claude Project on claude.ai. Any conversation in that project will have your full context.

Re-export after major context changes.

---

## Ongoing Use

### After sessions where things changed

If your priorities shifted, you met someone new, or you want to update a behavioral rule:

```
/ai-memory-sync push
```

Claude pushes your locally-updated files to Tana.

### If another LLM updated your Tana context

If another LLM edited your Tana nodes:

```
/ai-memory-sync pull
```

Claude pulls the Tana changes to your local files.

### Periodic enrichment (recommended monthly)

```
/ai-memory-sync enrich
```

Claude scans recent meetings and tasks, surfaces new people and themes, and asks if you want to update your memory nodes.

### After major life/work changes

New job, new team, new priorities:

```
/ai-memory-setup refresh
```

Re-runs the discovery phase and shows you what's changed. You approve which nodes to update.

---

## Troubleshooting

**"Tana MCP must be connected"**
- Run `/mcp` in Claude Code — it should show your Tana connection
- Check Tana's local API settings (top-right corner in Tana → API/MCP)

**Skill not found when running `/ai-memory-setup`**
- Verify the skill is in the right location: `~/.claude/skills/ai-memory-setup/SKILL.md`
- Restart Claude Code and try again

**"AI_Context tag already exists" but with wrong fields**
- The skill will read the existing tag's schema and adapt. If fields are missing, Claude will note them and you can decide whether to add them manually in Tana.

**Node content looks off after setup**
- Remember: content prefixed with "Inferred:" came from your knowledge graph. Edit it directly in Tana or via `/ai-memory-sync push` after updating local files.
