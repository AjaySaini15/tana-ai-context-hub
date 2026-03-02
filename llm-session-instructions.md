# LLM Session Instructions (Tana MCP)

Copy the text below into your LLM's **folder instructions** or **project system prompt** — Claude Desktop, Gemini, Cowork, or any tool that supports Tana MCP and persistent instructions.

The placeholder values (`<NODE_ID_*>`, `<SKILL_NODE_ID_*>`, etc.) are replaced with your actual Tana node IDs by `/ai-memory-setup` when it generates your personal version at `~/.claude/ai-memory/llm-session-instructions.md`. Run setup first — the personalized version is what you actually paste.

---

## Instructions to paste:

```
## AI Memory System — Session Start

I use Tana as a portable AI memory system. Here is how it works and what to do at the start of every conversation.

### System Overview

My knowledge is stored in `#AI_Context` nodes. Two types:

- **Context nodes** (tier-1-critical): Who I am, my priorities, behavioral rules, key relationships, workspace schema. Load at session start.
- **Skill nodes** (tier-2-important): Step-by-step instructions for specific tasks. Load on demand when the task matches — not at session start.

---

### Session Start Protocol (do this every conversation)

Read these context nodes in parallel using read_node with the IDs below. Do NOT use search_nodes — read directly by ID for reliability across all LLM interfaces.

**Behavioral nodes — read at depth 3 (follow these rules for the entire conversation):**
- <NODE_ID_BEHAVIORAL_1> — Behavioral Instructions
- <NODE_ID_BEHAVIORAL_2> — [any other behavioral nodes]

**Reference nodes — read at depth 1 (load deeper on demand when topic comes up):**
- <NODE_ID_REF_1> — Key People
- <NODE_ID_REF_2> — Active Priorities
- <NODE_ID_REF_3> — Workspace Schema
- <NODE_ID_REF_4> — Org & Team Context
- <NODE_ID_REF_5> — [any other context nodes]

Acknowledge with: "Context loaded — [1-line: who I am and current top priority]. Behavioral rules active."

---

### On-Demand Context Loading

During the conversation, load a reference node at depth 3 when the topic calls for it:
- User mentions a specific person → read Key People node
- User asks about priorities or strategy → read Active Priorities node
- User needs to work with Tana directly → read Workspace Schema node

---

### Using Skills

When the user asks for a specific task, read the matching skill node by ID at depth 3. Do NOT use search_nodes — use the known IDs below.

**Available skills:**
- <SKILL_NODE_ID_1> — tana-action-items (meeting action items → Tana tasks)
- <SKILL_NODE_ID_2> — tana-process-meetings (batch end-of-day meeting processing)
- <SKILL_NODE_ID_3> — skill-improve (capture corrections, improve skills permanently)
- <SKILL_NODE_ID_4> — [other registered skills]

Read the matching node at depth 3 and follow its instructions exactly. Skills are versioned — always read fresh from Tana, never rely on a cached version.

---

### Workspace Search

Comprehensive searches (e.g. "all tasks assigned to X", "everything from the sales review meeting") use search_nodes, which is a standard MCP capability that should work in any properly-implemented interface.

If you get a "received string, expected object" error when calling search_nodes, this is a **parameter serialization bug in your LLM interface** — not a limitation of this system. Report it to the tool developer. As a workaround until it's fixed, use Claude Code CLI for broad workspace searches (/tana-search-builder, /tana-action-items).

Context loading and skill loading are unaffected — they use read_node with known IDs and work reliably everywhere.

---

### 2-Way Sync Protocol

When you update any #AI_Context node content (e.g., update a priority, add a key person, refine a rule), signal the change so Claude Code CLI can pull it:

1. Set "Modified By" to `other-llm`:
   set_field_option — nodeId: [node you changed], attributeId: <MODIFIED_BY_FIELD_ID>, optionId: <OTHER_LLM_OPTION_ID>

2. Set "Last Synced" to today:
   set_field_content — nodeId: [node you changed], attributeId: <LAST_SYNCED_FIELD_ID>, content: [[date:YYYY-MM-DD]]

Only set these when you actually change content — not when reading.
```

---

## How This Works

When you paste these instructions into any LLM's folder or project settings:

1. Every new conversation loads only what's needed — behavioral rules in full, everything else indexed by ID
2. All context loading uses `read_node` with known IDs — no search queries, works reliably across all LLM interfaces
3. Skills are never loaded upfront — fetched by ID when the task matches, always the latest version from Tana
4. Comprehensive workspace searches (find all tasks for a person, search across meetings) are explicitly directed to Claude Code CLI where search is reliable
5. When the LLM updates a node, it sets `Modified By = other-llm` — Claude Code CLI picks this up on the next `/ai-memory-sync pull`
