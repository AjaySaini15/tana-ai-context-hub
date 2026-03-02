---
name: ai-memory-setup
description: Bootstrap self-updating AI memory in Tana. Reads your knowledge graph, creates an #AI_Context framework for context AND skills, and generates a sync manifest for ongoing 2-way sync. Run once to set up, periodically to refresh.
argument-hint: "[setup|refresh|status]"
---

# Skill: AI Memory Setup

Bootstrap a self-improving AI system in Tana. This skill reads your existing Tana knowledge graph, learns your workspace structure and key relationships, interviews you with 3 targeted questions, then creates a portable `#AI_Context` framework — for both your context (who you are, your priorities) AND your skills (your procedural AI knowledge).

Once set up:
- Your context lives in Tana, readable by any LLM with Tana MCP
- Your skills live in Tana, versioned and improvable from any LLM
- `/ai-memory-sync` keeps everything current
- `/skill-improve` captures corrections and makes skills smarter over time

## Modes

| Argument | Behavior |
|----------|----------|
| `setup` (default) | Full discovery → interview → create context nodes → bootstrap skills → write manifest |
| `refresh` | Re-discover recent activity, update existing nodes (no re-interview unless major changes) |
| `status` | Report what's in the AI Context Hub — no changes made |
| `export` | Export all tier-1 nodes to a single markdown file for mobile/offline LLM access |

---

## Phase 1: Discover the Workspace

### 1a. Get Workspace Entry Point
```
list_workspaces → get workspaceId and home node ID
```

### 1b. Discover All Tags
```
list_tags → get all supertags with names, IDs, and node counts
```

From the results, identify tags in these categories by scanning names:

| Category | Look for names like... |
|----------|------------------------|
| Meeting | "Meeting", "1:1", "Call", "Review", "Standup" |
| Task / Action | "Task", "Todo", "Action Item", "Next Action" |
| Person / Contact | "Person", "Contact", "People", "Stakeholder" |
| Project / Initiative | "Project", "Initiative", "Goal", "OKR" |
| Note / Journal | "Note", "Daily", "Journal", "Log", "Entry" |

For each identified tag: call `get_tag_schema` to record field names, types, and option values.

### 1c. Sample Recent Content

Run these searches in parallel:

1. **Recent meetings** — `search_nodes` with `{ "hasType": "<meeting_tag_id>" }` → take the most recent 10 → `read_node` each at depth 1
2. **Open tasks** — `search_nodes` with `{ "hasType": "<task_tag_id>" }` → take the most recent 20 → scan for assignee patterns, common contexts
3. **People** — `search_nodes` with `{ "hasType": "<person_tag_id>" }` → get up to 50 names

From meeting nodes, extract:
- **Recurring participant names** (appearing in 3+ meetings = key relationship)
- **Recurring topics/themes** (appearing in 3+ meetings = likely priority area)
- **Meeting cadence** (daily / weekly / ad-hoc)

### 1d. Discover Skills Across All Tools

Ask the user which AI tools they use and where their skills/prompts live:

> "I'll set up skill sync across all your AI tools. Which of these do you use?
> (Select all that apply — I'll scan each location)
>
> 1. **Claude Code CLI** — skills in `~/.claude/skills/`
> 2. **Gemini CLI** — prompts folder (tell me the path)
> 3. **A custom folder** — I keep my prompts in (tell me the path)
> 4. **None yet** — I'll start from scratch in Tana, sync to tools later"

For each confirmed tool + path, scan the directory for skill files:
- Claude Code: look for `*/SKILL.md` in subdirectories
- Generic: look for `*.md` or `*/skill.md` files
- For each found: read the file — note name, description, approximate purpose

Store discovered tools and paths as `skillPaths` in the manifest (see Phase 6).

**If the user selects "None yet":** Skip skill bootstrapping. Skills will be authored directly in Tana and synced out to tools on demand via `/ai-memory-sync pull`.

### 1e. Build Discovery Report (internal)

```
Workspace discovered:
- [N] supertags. Meeting: [tag], Task: [tag], Person: [tag], Project: [tag]
- [N] recent meetings. Most recent: "[title]"
- Recurring people: [Name A] (in X meetings), [Name B] (Y), [Name C] (Z)
- Recurring themes: [theme 1], [theme 2], [theme 3]
- [N] open tasks
- [N] existing skills found: [skill-name-1], [skill-name-2], ...
```

---

## Phase 2: Targeted Interview

Present the discovery report to the user, then ask exactly 3 questions. Use what you discovered to make them specific.

> I've explored your Tana workspace. Here's what I found:
> - **[N] meeting types**, most recent: "[meeting title]"
> - **Recurring people**: [Name A], [Name B], [Name C]
> - **Active themes**: [theme 1], [theme 2]
> - **[N] skills** already built: [skill-name-1], [skill-name-2], ...
>
> Three quick questions to personalize your AI memory:

**Q1 — Role & Goal:**
> "In one or two sentences — what's your role and your most important goal right now?"

**Q2 — Key Relationships:**
> "I found these people appearing frequently: [Name A], [Name B], [Name C]. Who are the 3–5 relationships that matter most, and what's your relationship with each?"

**Q3 — Behavioral Rules:**
> "What's one rule you want your AI to always follow when working with you?"

Wait for all three answers before proceeding.

---

## Phase 3: Update #AI_Context Schema

### Check if #AI_Context tag exists

`list_tags` → search for "AI_Context" or "AI Context".

**If exists:** `get_tag_schema` → record all field IDs and option IDs. Check that these fields are present: Context Type, Priority Tier, Last Synced, Modified By, Local File Path, Version. If Version field is missing, note it — the user can add it manually or Claude can suggest adding it.

**If doesn't exist:** create via `import_tana_paste` under the home node:

```
%%tana%%
- #supertag AI_Context
  - Context Type:: #field options
    - behavioral
    - schema
    - memory
    - reference
    - skill
  - Priority Tier:: #field options
    - tier-1-critical
    - tier-2-important
    - tier-3-reference
  - Last Synced:: #field date
  - Modified By:: #field options
    - claude-code
    - other-llm
    - manual
  - Local File Path:: #field url
  - Version:: #field plain
```

After creating: `list_tags` → find new tag → `get_tag_schema` → record all field IDs and option IDs.

### Create AI Context Hub container

Create a container node in Library:

```
%%tana%%
- AI Context Hub
  - Setup by Claude Code on [today]
  - Context nodes: load at session start (tier-1-critical)
  - Skill nodes: load on demand or when running that skill
  - To sync: /ai-memory-sync | To improve a skill: /skill-improve [name]
```

Record hub node ID for manifest.

---

## Phase 4: Create Context Nodes (Tier-1)

Create 5 context nodes under the AI Context Hub. Populate from discovery + interview answers.

**Node 1: About Me**
```
%%tana%%
- About Me #AI_Context
  - Context Type:: behavioral
  - Priority Tier:: tier-1-critical
  - Modified By:: claude-code
  - Version:: v1.0
  - Role & Goal
    - [User's answer to Q1]
  - Key Relationships
    - [Person from Q2] — [relationship]
    - [Additional high-frequency people, labeled "Inferred:"]
  - Timezone & Preferences
    - [Any inferred or stated preferences]
```

**Node 2: Workspace Schema**
```
%%tana%%
- Workspace Schema #AI_Context
  - Context Type:: schema
  - Priority Tier:: tier-1-critical
  - Modified By:: claude-code
  - Version:: v1.0
  - Tags & Fields
    - [Meeting tag] (id: [tag_id])
      - [field]: [type] — [options]
    - [Task tag] (id: [tag_id])
      - [field]: [type] — [options]
    - [Person tag], [Project tag] similarly
  - Conventions Observed
    - [Inferred patterns]
```

**Node 3: Key People**
```
%%tana%%
- Key People #AI_Context
  - Context Type:: reference
  - Priority Tier:: tier-1-critical
  - Modified By:: claude-code
  - Version:: v1.0
  - [Person A] — [role from Q2]
    - Met [N] times recently. Topics: [inferred]
  - [Person B] — [role from Q2]
  - [High-frequency people from discovery, labeled "Inferred:"]
```

**Node 4: Active Priorities**
```
%%tana%%
- Active Priorities #AI_Context
  - Context Type:: memory
  - Priority Tier:: tier-1-critical
  - Modified By:: claude-code
  - Version:: v1.0
  - Current Priorities
    - [From Q1 answer + inferred from meeting themes]
  - Open Projects (Inferred)
    - [From task clusters]
  - Last refreshed: [today]
```

**Node 5: AI Behavioral Rules**
```
%%tana%%
- AI Behavioral Rules #AI_Context
  - Context Type:: behavioral
  - Priority Tier:: tier-1-critical
  - Modified By:: claude-code
  - Version:: v1.0
  - Rules
    - [Rule from Q3]
    - When creating tasks: use #[task tag] with all required fields
    - When context is stale (>7 days): flag and suggest /ai-memory-setup refresh
    - When a skill produces wrong output and is corrected: offer /skill-improve
  - Session Start Protocol
    - Load all #AI_Context nodes tagged tier-1-critical at depth 3
```

---

## Phase 5: Bootstrap Skills into Tana

This is what transforms the system from "context sync" to "self-improving skills."

### 5a. Deduplicate across tools

Skills discovered from multiple tool paths may overlap (same skill exists in Claude AND a generic folder). Deduplicate by name — ask the user which version to use as the canonical source when duplicates exist.

### 5b. Present consolidated skills list

> "I found [N] skills across your tools:
>
> From Claude Code (~/.claude/skills/):
>   tana-action-items — Process meeting transcripts, extract tasks
>   tana-process-meetings — Batch process all meetings
>   ...
>
> From [other tool] ([path]):
>   my-weekly-review — Generate weekly review from notes
>   ...
>
> Should I add these to Tana? Once there:
>   - Any LLM with Tana MCP reads the latest version directly
>   - /skill-improve tracks every correction with version history
>   - /ai-memory-sync push/pull keeps all tool paths current"

### 5c. Create a skill node for each

Skills in Tana are **tool-agnostic by design**. The Tana node stores intent and instructions in plain language — tool-specific formatting stays in local files. This is what makes the node readable by Gemini, Claude Desktop, or any future LLM with Tana MCP.

For each skill, create under the AI Context Hub:

```
%%tana%%
- [Skill Name] #AI_Context
  - Context Type:: skill
  - Priority Tier:: tier-2-important
  - Modified By:: claude-code
  - Version:: v1.0

  - Purpose
    - [What this skill does — one paragraph, plain language, tool-agnostic]
    - When to use: [trigger conditions in plain language]

  - Eval Criteria
    - [What good output looks like]
    - [Known failure modes this skill should NOT produce]

  - Skill Content
    - [Full instructions, broken into sections as child nodes]
    - [Each ## heading becomes a child node]
    - [Content is tool-agnostic where possible; tool-specific notes go in sub-nodes labeled "Claude Code:", "Gemini:", etc.]

  - Tool Paths
    - claude-code:: ~/.claude/skills/[name]/SKILL.md
    - [other-tool]:: [path]

  - Change Log
    - v1.0 ([today]) — Initial version. Bootstrapped from [source tool] by /ai-memory-setup.
```

### 5d. Infer Eval Criteria

For each skill, read the content and infer what "success" looks like:
- Creates Tana nodes → "correct nodes created with all required fields populated"
- Analyzes text/transcripts → "findings cited with direct quotes from source"
- Syncs files → "source and destination match after execution; no data lost"
- Generates structured output → "output matches expected schema; no missing sections"

These seed Eval Criteria. They get refined over time via `/skill-improve`.

---

## Phase 6: Generate Sync Manifest

Write `~/.claude/ai-memory/sync-manifest.json`:

```json
{
  "version": 1,
  "workspaceId": "<workspace_id>",
  "hubNodeId": "<hub_node_id>",
  "setupDate": "<today>",
  "skillPaths": [
    {
      "tool": "claude-code",
      "directory": "~/.claude/skills/",
      "filePattern": "[name]/SKILL.md",
      "format": "claude-skill-md"
    },
    {
      "tool": "gemini-cli",
      "directory": "<user-provided path or omit if not used>",
      "filePattern": "[name].md",
      "format": "generic-md"
    },
    {
      "tool": "generic",
      "directory": "~/.ai-skills/",
      "filePattern": "[name]/skill.md",
      "format": "generic-md"
    }
  ],
  "schema": {
    "tagId": "<ai_context_tag_id>",
    "fields": {
      "contextType": "<field_id>",
      "priorityTier": "<field_id>",
      "lastSynced": "<field_id>",
      "modifiedBy": "<field_id>",
      "localFilePath": "<field_id>",
      "version": "<field_id>"
    },
    "optionIds": {
      "modifiedBy": {
        "claude-code": "<option_id>",
        "other-llm": "<option_id>",
        "manual": "<option_id>"
      },
      "priorityTier": {
        "tier-1-critical": "<option_id>",
        "tier-2-important": "<option_id>",
        "tier-3-reference": "<option_id>"
      },
      "contextType": {
        "behavioral": "<option_id>",
        "schema": "<option_id>",
        "memory": "<option_id>",
        "reference": "<option_id>",
        "skill": "<option_id>"
      }
    }
  },
  "nodes": {
    "<about_me_node_id>": {
      "name": "About Me",
      "localPath": "~/.claude/ai-memory/about-me.md",
      "section": "entire-file",
      "lastSyncedLocal": "<ISO timestamp: YYYY-MM-DDTHH:MM:SS>",
      "tier": "tier-1-critical",
      "contextType": "behavioral",
      "version": "v1.0"
    },
    "<workspace_schema_node_id>": {
      "name": "Workspace Schema",
      "localPath": "~/.claude/ai-memory/workspace-schema.md",
      "section": "entire-file",
      "lastSyncedLocal": "<ISO timestamp: YYYY-MM-DDTHH:MM:SS>",
      "tier": "tier-1-critical",
      "contextType": "schema",
      "version": "v1.0"
    },
    "<key_people_node_id>": {
      "name": "Key People",
      "localPath": "~/.claude/ai-memory/key-people.md",
      "section": "entire-file",
      "lastSyncedLocal": "<ISO timestamp: YYYY-MM-DDTHH:MM:SS>",
      "tier": "tier-1-critical",
      "contextType": "reference",
      "version": "v1.0"
    },
    "<active_priorities_node_id>": {
      "name": "Active Priorities",
      "localPath": "~/.claude/ai-memory/active-priorities.md",
      "section": "entire-file",
      "lastSyncedLocal": "<ISO timestamp: YYYY-MM-DDTHH:MM:SS>",
      "tier": "tier-1-critical",
      "contextType": "memory",
      "version": "v1.0"
    },
    "<behavioral_rules_node_id>": {
      "name": "AI Behavioral Rules",
      "localPath": "~/.claude/ai-memory/behavioral-rules.md",
      "section": "entire-file",
      "lastSyncedLocal": "<ISO timestamp: YYYY-MM-DDTHH:MM:SS>",
      "tier": "tier-1-critical",
      "contextType": "behavioral",
      "version": "v1.0"
    },
    "<skill_node_id_1>": {
      "name": "[Skill Name 1]",
      "localPath": "~/.claude/skills/[skill-name-1]/SKILL.md",
      "section": "entire-file",
      "lastSyncedLocal": "<ISO timestamp: YYYY-MM-DDTHH:MM:SS>",
      "tier": "tier-2-important",
      "contextType": "skill",
      "version": "v1.0"
    }
  }
}
```

**Shared-file context nodes** — when multiple context nodes map to sections of the same file (e.g., CLAUDE.md), add section boundary fields to each manifest entry:
```json
"sectionStart": "<exact heading text that starts this section>",
"sectionEnd": "<exact heading text of the next section, or null for EOF>",
"sectionHash": null
```
`sectionHash` starts as null and is populated on the first `/ai-memory-sync check` run. This enables surgical push: editing one section of a shared file only pushes that section's Tana node.

Also write local markdown copies of each context node's content to their respective local paths.
Generate `~/.claude/ai-memory/llm-session-instructions.md` with all placeholders replaced with real values:
- `<NODE_ID_BEHAVIORAL_*>` → actual node IDs of all contextType=behavioral nodes, with their names
- `<NODE_ID_REF_*>` → actual node IDs of all other tier-1 context nodes, with their names
- `<SKILL_NODE_ID_*>` → actual node IDs of all registered skill nodes, with skill names and descriptions
- `<MODIFIED_BY_FIELD_ID>` → Modified By field ID
- `<OTHER_LLM_OPTION_ID>` → other-llm option ID
- `<LAST_SYNCED_FIELD_ID>` → Last Synced field ID

The personalized version uses read_node with hardcoded IDs everywhere — no search_nodes calls. This ensures reliable context loading across all LLM interfaces regardless of how they handle JSON query parameters.

---

## Phase 7: Report

```
AI Memory Setup Complete!

Context (who you are):
  ✓ About Me
  ✓ Workspace Schema
  ✓ Key People
  ✓ Active Priorities
  ✓ AI Behavioral Rules

Skills (how your AI works):
  ✓ [skill-name-1] — v1.0 (bootstrapped)
  ✓ [skill-name-2] — v1.0 (bootstrapped)
  ✓ [skill-name-3] — v1.0 (bootstrapped)

All nodes are in Tana (Library > AI Context Hub) and locally synced.

Next:
  /ai-memory-sync          — keep everything in sync
  /skill-improve [name]    — capture a correction and improve a skill
  /ai-memory-sync export   — generate mobile-ready markdown
  /ai-memory-setup refresh — re-discover after major changes

Every time a skill gets corrected and improved, /skill-improve
updates the Tana node and logs the change. Your AI gets smarter
over time — and the record lives in Tana.
```

---

## Refresh Mode

When called with `refresh`:

1. Re-run Phase 1 (discovery) — check for new tags, people, themes
2. Scan `~/.claude/skills/` — any new skills added since last setup?
3. For each skill in manifest: check if local version > Tana version (local was updated without pushing)
4. Present diff: "Here's what's new since your last setup"
5. On confirmation: update nodes, bump versions, log changes, update manifest

---

## Important Rules

- **Never duplicate.** Always check for existing #AI_Context tag and nodes before creating.
- **Label inferences.** Content derived from the graph (not from user answers) is prefixed "Inferred:" so the user knows.
- **Skills need eval criteria.** Even if inferred — better a rough eval than none. It seeds the improvement loop.
- **Node IDs after creation.** After `import_tana_paste`, search by name to find the new node's ID for the manifest.
- **If Tana MCP not connected:** stop and say "Tana MCP must be connected. Check /mcp."
