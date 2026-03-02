---
name: ai-memory-sync
description: 2-way sync between local AI context/skill files and Tana #AI_Context nodes. Handles both context (who you are) and skills (how your AI works). Tracks versions, detects which side changed, syncs accordingly.
argument-hint: "[check|pull|push|register|enrich|export|export all]"
---

# Skill: AI Memory Sync

Keep your entire AI system in sync — both context nodes and skill nodes — between local files and Tana. The `Modified By` field signals which side changed. This skill reads those signals and syncs accordingly, including version increments and change log updates for skills.

## Prerequisites

- Run `/ai-memory-setup` first to create the framework and generate `~/.claude/ai-memory/sync-manifest.json`
- Tana MCP must be connected

## Modes

| Argument | Behavior |
|----------|----------|
| `check` (default) | Report sync status for all nodes — what's stale, in which direction |
| `pull` | Pull all nodes modified by other LLMs (Tana → local files) |
| `push` | Push all locally-modified files (local → Tana), with version increment |
| `register` | Scan local skill paths for new skills not in manifest — create Tana nodes and register them |
| `enrich` | Scan recent Tana activity, suggest updates to context AND skill nodes |
| `export` | Export tier-1 context nodes to a single markdown file (for mobile) |
| `export all` | Export tier-1 + tier-2 nodes (includes skills) |

---

## Step 1: Load Manifest

Read `~/.claude/ai-memory/sync-manifest.json`.

Contains:
- `schema` — tag ID, all field IDs, all option IDs
- `nodes` — map of Tana node IDs → local paths, last sync dates, versions, context types

If no manifest: tell user to run `/ai-memory-setup` first.

## Step 2: Check All Nodes

**2a. Check manifest nodes** — for each node in the manifest, `read_node` at depth 0 to get:
- **Last Synced** — when the node was last updated in Tana
- **Modified By** — who last changed it
- **Version** — current version in Tana

Run all reads in parallel. Also check local files:

- **Nodes with `sectionStart`** (context nodes sharing a file): extract the section content (from `sectionStart` heading to `sectionEnd` heading, or EOF if `sectionEnd` is null), compute a hash of it, compare to `sectionHash` in manifest. If `sectionHash` is null in manifest, compute and store it now — do NOT treat as needing push on first run.
- **Nodes without `sectionStart`** (entire-file nodes): compare file mtime against `lastSyncedLocal` ISO timestamp as before.

**2b. Discover new Tana nodes** — search for ALL `#AI_Context` nodes in Tana:
```json
{ "hasType": "JiS23yeW9-kN" }
```
Compare returned node IDs against manifest keys. Any node returned by Tana that is **not in the manifest** is a candidate. Read it at depth 1 to check its fields.

**Only flag as NEW IN TANA if the node has both `Context Type` AND `Priority Tier` fields set.** Child nodes (change log entries, key steps, etc.) inherit the `#AI_Context` tag from their parent but have no fields — they are not real context nodes and must be silently skipped.

## Step 3: Determine Sync Direction

For each node:

```
NEEDS PULL (Tana → Local):
  Modified By = "other-llm" OR "manual"
  AND Last Synced > lastSyncedLocal in manifest

NEEDS PUSH (Local → Tana):
  For section-based nodes (have sectionStart): current sectionHash ≠ manifest sectionHash
  For entire-file nodes: file mtime > lastSyncedLocal ISO timestamp in manifest
  AND (both cases) Modified By ≠ "other-llm"

IN SYNC:
  Tana Last Synced = manifest lastSyncedLocal AND no local changes

CONFLICT:
  Both sides modified since last sync
  → Show both versions, ask user which to keep
```

**Timestamp precision:** `lastSyncedLocal` is stored as ISO 8601 (`YYYY-MM-DDTHH:MM:SS`), not date-only. Use `stat` to get file mtime as a comparable timestamp. Date-only granularity causes false "in sync" results when multiple changes happen on the same day.

**Section extraction:** For nodes with `sectionStart` in the manifest, extract content from the file starting at the line matching `sectionStart` and ending at the line before `sectionEnd` (or EOF if `sectionEnd` is null). This means editing one section of a shared file only pushes that section's Tana node — not all nodes that share the file.

## Step 4: Report Status Table

Always show before acting:

```
AI Memory Sync — 2026-03-01
─────────────────────────────────────────────────────────────────
CONTEXT NODES
Node                  Version  Status      Modified By   Action
─────────────────────────────────────────────────────────────────
About Me              v1.2     ✓ In sync   claude-code   —
Workspace Schema      v1.0     ← PULL      other-llm     Tana → Local
Key People            v1.1     ✓ In sync   claude-code   —
Active Priorities     v1.3     → PUSH      claude-code   Local → Tana
AI Behavioral Rules   v1.1     ✓ In sync   claude-code   —

SKILL NODES
Node                  Version  Status      Modified By   Action
─────────────────────────────────────────────────────────────────
tana-action-items     v2.1     → PUSH      claude-code   Local → Tana
ai-memory-setup       v1.0     ✓ In sync   claude-code   —
skill-improve         v1.1     ← PULL      other-llm     Tana → Local

NEW IN TANA (not yet local)
Node                  Version  Type        Action
─────────────────────────────────────────────────────────────────
weekly-review         v1.0     skill       → pull to create SKILL.md
competitor-brief      v1.0     context     → pull to create local file
─────────────────────────────────────────────────────────────────
5 actions needed. Proceed? (pull/push/all/cancel)
```

For `check` mode: stop here.

---

## Executing Pull (Tana → Local)

### Existing nodes (in manifest)

For each node that needs pulling:

1. `read_node` at depth 3 — get full content
2. For **context nodes**: convert to clean markdown (strip metadata fields, tag references, node-id comments)
3. For **skill nodes**: reconstruct SKILL.md format:
   - Extract front matter from node metadata (name, description, argument-hint)
   - Extract body content from "Skill Content" section
   - Do NOT include Eval Criteria or Change Log in local SKILL.md (those live in Tana only)
   - Wrap in proper SKILL.md format with `---` front matter
4. Write to `localPath`
5. Update manifest: `lastSyncedLocal` = current ISO timestamp (YYYY-MM-DDTHH:MM:SS), `version` = Tana version
6. Set Tana node: `Last Synced` = today. **Do NOT change `Modified By`** — leave it as `other-llm`/`manual` to preserve attribution of who authored the change.

### New nodes (in Tana, not yet in manifest)

For each NEW IN TANA node:

1. `read_node` at depth 3 — get full content and metadata
2. Determine `contextType` from node fields
3. **For skill nodes:**
   - Reconstruct SKILL.md as above
   - Default local path: `~/.claude/skills/[skill-name]/SKILL.md` (first entry in `manifest.skillPaths`)
   - Write to ALL configured tool paths in their respective formats
4. **For context nodes:**
   - Convert to clean markdown
   - Suggest a local path: `~/.claude/ai-memory/[node-name-slug].md`
   - Confirm path with user before writing
5. Add to manifest with the node ID, local path, current ISO timestamp (YYYY-MM-DDTHH:MM:SS), version from Tana
6. Set Tana node: `Last Synced` = today. **Do NOT change `Modified By`**.

Report per new node:
```
Pulled new skill: weekly-review
  ✓ Created ~/.claude/skills/weekly-review/SKILL.md
  ✓ Added to manifest
  ✓ Available as /weekly-review in Claude Code
```

## Inline Push (Primary Path for Context Changes)

Context changes made during a Claude Code session should be pushed to Tana **immediately in the same session** — not deferred to a later `/ai-memory-sync push` run. Claude Code has Tana MCP open; use it inline, the same way task creation works.

When Claude Code edits a file tracked in the manifest:
1. Identify the manifest entry (match by `localPath`)
2. Extract the changed section using `sectionStart`/`sectionEnd`
3. Push to Tana (see Context nodes push steps below)
4. Update `sectionHash` and `lastSyncedLocal` in manifest immediately

`/ai-memory-sync push` is the **bulk/recovery path** — use it when inline push was skipped (e.g., MCP unavailable, batch of changes at session end, or pulling in changes from another tool path).

---

## Executing Push (Local → Tana)

For each node that needs pushing:

### Context nodes:
1. Read local file
2. If node has `sectionStart` in manifest: extract only the section from `sectionStart` heading to `sectionEnd` heading (exclusive), or EOF if `sectionEnd` is null. **Never push the entire shared file to a single context node.**
   If no `sectionStart`: use entire file content.
3. Convert extracted content to Tana Paste (hierarchical `- ` prefixed nodes, 2-space indent)
4. `get_children` on Tana node — find content children (not field children)
5. `trash_node` for each content child
6. `import_tana_paste` with extracted content under the node
7. Set `Modified By` = `claude-code`, `Last Synced` = today
8. Update manifest: `lastSyncedLocal` = current ISO timestamp, `sectionHash` = hash of pushed section content

### Skill nodes (version-aware, multi-tool):

Skill pushes update Tana AND write out to every configured tool path in `manifest.skillPaths`.

1. Determine the **source** — which local file changed? Read `manifest.skillPaths` to find which tool it came from.
2. Read the changed local file.
3. **Update Tana node:**
   - `get_children` on skill node → find "Skill Content" child
   - Use `edit_node` for changed sections (surgical, not trash-and-recreate)
   - Increment version: patch bump (v1.2 → v1.3) via `set_field_content`
   - Append to Change Log:
     ```
     %%tana%%
     - [new_version] ([today]) — Synced from [tool] update. Run /skill-improve to add rationale.
     ```
   - Set `Modified By` = `claude-code`, `Last Synced` = today
4. **Write to all other tool paths** (cross-tool propagation):
   For each entry in `manifest.skillPaths` that is NOT the source tool:
   - Read the Tana node content
   - Convert to that tool's format:

     | format | Output |
     |--------|--------|
     | `claude-skill-md` | `---\nname: ...\ndescription: ...\n---\n\n# Skill: ...\n[content]` |
     | `generic-md` | Plain markdown, no front matter, just `# [Name]\n[content]` |
     | `json-prompt` | `{"name": "...", "description": "...", "instructions": "..."}` |

   - Write to `[directory]/[filePattern with name substituted]`
   - Create directories if they don't exist
5. Update manifest: `lastSyncedLocal` = today, `version` = new version for all tool paths

**Note:** If `/skill-improve` just ran, it passes the rationale — use that in the change log instead of the generic message.

**On pull (Tana → local):** Same logic in reverse — read Tana node, write to ALL configured tool paths in their respective formats. One Tana update propagates everywhere.

---

## Enrich Mode

Scan recent Tana activity to suggest updates to both context and skill nodes.

### For context nodes:

1. Search meetings from last 30 days — new recurring people or themes?
2. Search open tasks — new project clusters?
3. Search new person nodes added since last sync

### For skill nodes:

1. Check each skill node's Change Log — any improvements logged by other LLMs since last sync?
2. Check if any skill's "Eval Criteria" section has been updated in Tana (Modified By = other-llm)
3. Compare skill versions: Tana version vs manifest version

Present consolidated findings:

```
Enrich findings (since 2026-02-28):

CONTEXT:
  → New person in meetings: [Name X] (4 meetings) — add to Key People?
  → New theme emerging: "[theme]" (6 meetings) — add to Active Priorities?

SKILLS:
  → tana-action-items: Eval Criteria updated in Tana by other-llm — pull?
  → skill-improve: Change log has 2 new entries from other sessions — pull?

Proceed with which updates?
```

---

## Export Mode

Generate consolidated markdown for Claude Projects (mobile) or any LLM without Tana MCP.

### export (tier-1 context only):
- Read the 5 context nodes at depth 3
- Clean and concatenate into `~/.claude/ai-memory/ai-context-export.md`

### export all (tier-1 + tier-2 including skills):
- Read all nodes from manifest
- Clean and concatenate, with skills in a separate "## Skills" section:

```markdown
# AI Memory Export
> Exported [date]. Upload to Claude Project for mobile access.

---
## About Me
[content]

## Key People
[content]

...

---
# Skills

## tana-action-items (v2.1)
[skill content — instructions only, no change log]

## ai-memory-setup (v1.0)
[skill content]
```

Report: "Exported [N] nodes to ~/.claude/ai-memory/ai-context-export.md"

---

## Register Mode

Closes the loop for skills created locally after initial setup — by `/skill-creator`, manually, or by any other means.

### Step 1: Find unregistered skills

Read `manifest.skillPaths`. For each configured tool path:
- Expand the directory (e.g. `~/.claude/skills/`)
- List all subdirectories matching the `filePattern` pattern (e.g. each folder containing a `SKILL.md`)
- Extract the skill name from the folder/file name

Compare against all manifest entries with `contextType: "skill"`. Anything on disk but not in the manifest is **unregistered**.

### Step 2: Report findings

```
Unregistered skills found:
  • daily-standup       ~/.claude/skills/daily-standup/SKILL.md
  • competitor-tracker  ~/.claude/skills/competitor-tracker/SKILL.md

Register these in Tana? They'll get a node in the AI Context Hub with version tracking and change log. (yes/no/select)
```

If nothing new: "All local skills are already registered. Nothing to do."

### Step 3: For each skill to register

1. **Read the local SKILL.md** — extract front matter: `name`, `description`, `argument-hint`
2. **Create Tana node** under the hub (`hubNodeId` from manifest):

```
%%tana%%
- [skill-name] #[[^JiS23yeW9-kN]]
  - [[^YRi6GC8s0sq-]]:: [[^7IR-cxldk2qC]]
  - [[^JJUXVXR2eyzc]]:: [[^yz3xDbE91cWL]]
  - [[^qOyRR8O_MMpj]]:: [[^3xuSpzpzMAK-]]
  - [[^PyhHsBeJ9yyU]]:: [[date:YYYY-MM-DD]]
  - [[^a5x6ZkzCHDrV]]:: [localPath]
  - Purpose
    - [description from front matter]
  - Eval Criteria
    - What good output looks like (fill in based on skill content)
    - Known failure modes this skill should NOT produce
  - Skill Content
    - [full SKILL.md body, section by section as child nodes]
  - Change Log
    - v1.0 ([today]) — Initial registration. Skill created locally before being added to Tana.
```

3. **Capture the new node ID** returned by `import_tana_paste`
4. **Write to all other configured tool paths** in `manifest.skillPaths` (cross-tool propagation — same as push)
5. **Add to manifest:**
```json
"<new_node_id>": {
  "name": "[skill-name]",
  "localPath": "~/.claude/skills/[skill-name]/SKILL.md",
  "section": "entire-file",
  "lastSyncedLocal": "<today>",
  "tier": "tier-2-important",
  "contextType": "skill",
  "version": "v1.0"
}
```

### Step 4: Confirm

```
Registered: daily-standup
  ✓ Tana node created (id: <node_id>)
  ✓ Manifest updated
  ✓ Available to all LLMs with Tana MCP from next session

Registered: competitor-tracker
  ✓ Tana node created (id: <node_id>)
  ✓ Manifest updated
```

---

## Important Rules

- **Skills get version increments on push.** Every time a skill is pushed to Tana, bump the version. This creates an audit trail.
- **Don't overwrite Change Log.** When pushing a skill, only append to the Change Log — never replace existing entries.
- **Field children are not content children.** When trashing content to replace it, identify field nodes (matching schema field IDs) and skip them.
- **Conflict resolution asks the user.** Never silently pick a version when both sides changed.
- **Skill content vs skill metadata.** The Change Log and Eval Criteria live only in Tana — they're not in the local SKILL.md. Don't try to pull them into the local file.
- **Always show status before acting.** Even for `push` and `pull`, show the table and ask for confirmation.
