---
name: tana-understand
description: Explore a specific part of your Tana system — a tag, workflow, or subsystem — and show how Claude can help you work with it.
argument-hint: "[tag, workflow, or subsystem]"
---

# Skill: Understand Tana System

Explore a **specific part** of your Tana system — a tag, workflow, or subsystem — and show how Claude can help work with it.

> The examples below use the shared demo workspace (`demo-workspace/DEMO-WORKSPACE.md`):
> people **Riya Sharma** / **Tom Becker** / **Maya Chen**, a `#Task` tag (`demoTaskTag1`),
> a `#Meeting` tag (`demoMeetTag1`), and so on. Every `demo…` ID is a placeholder — swap in
> your own (see [GETTING-STARTED.md](../../GETTING-STARTED.md) → "Finding your own IDs").

## When to Use

The user asks to understand, explore, document, or analyze a specific tag, workflow, or subsystem in Tana.

## Key Principle: Stay Focused

**This skill is NOT for exploring an entire workspace.** It's for understanding specific parts:
- A particular tag and its inheritance/usage (e.g. "explain my `#Task` tag")
- A workflow (e.g. "how do I get from a meeting to action items?")
- A subsystem (e.g. "my meeting-notes setup")
- A related group of tags (e.g. "all my project-related tags")

**Always start by identifying the specific focus.** If the user says "understand my Tana" or something equally vague, ask what specific part they want to explore before doing anything else.

## Process

Use a cheap subagent (e.g. a Haiku-class model) for the raw exploration, but this is not rote lookup — it requires reasoning about what you find and making smart decisions about what to explore next. The goal is to genuinely understand how the user has built their system and how they use it.

### Tools for Exploration

| Tool | Use |
|------|-----|
| `list_workspaces` | Find available workspaces |
| `list_tags` | See what tag systems exist |
| `get_tag_schema` | Understand tag structure, fields, inheritance |
| `search_nodes` | Find nodes by text, tag, or properties; surface usage patterns |
| `read_node` | Read node content and children |
| `get_children` | Paginated children for large nodes |

### 1. Discover What Exists

**Start by understanding the workspace:**
1. `list_workspaces` to find available workspaces.
2. `list_tags` on the relevant workspace to see what systems exist.

This reveals what the user has built and informs what options to present.

### 2. Identify Focus

**If the user hasn't specified what to explore, use `AskUserQuestion` with options informed by the tags you just discovered.** This gives the user relevant choices rather than generic ones — e.g. if `list_tags` returned `#Task`, `#Meeting`, and `#Decision`, offer those as the options.

Don't explore broadly without a clear target.

### 3. Discover Structure

**Find the entry point:**
- If the user names a tag: `search_nodes` with `textContains` to find it (look for `docType: "tagDef"`).
- If the user describes a workflow: identify the key tag(s) involved.

**Understand a tag:**
- `get_tag_schema` returns fields, types, options, defaults, and parent tags.
- Use `includeEditInstructions: true` for additional context.

**Trace inheritance:**
- Upward: `get_tag_schema` shows "Extends #…" — chain calls to trace ancestry.
- Downward: `search_nodes` with `{"and": [{"hasType": "<tag-id>"}, {"is": "template"}]}`.

**Read context:**
- `read_node` with `maxDepth: 2-3` for documentation nodes, dashboards, and examples.

**Understand usage:**
- How many instances exist? (`search_nodes` with a tag filter.)
- Are fields consistently filled in, or often left blank?
- What patterns emerge in how the user works with this system?
- Are there related searches, views, or dashboards?

### 4. Document Findings

Present clearly:
- Tag names with their IDs (actionable references the user can reuse).
- A visual hierarchy showing inheritance.
- Key fields and their purposes.
- How the system is meant to be used.

Offer to save this to a markdown file.

### 5. Present How I Can Help

After understanding the structure, explain what you and the user can do together. This is where the real value emerges.

**Adapt to the system.** Based on what the system is designed to do, identify specific ways you can help. Think: what queries, preparations, or processing would be valuable for *this* setup?

**Be concrete.** Don't list abstract capabilities — give specific examples the user can try immediately, grounded in their actual tags and data.

**Offer to demonstrate.** End with 2–3 specific things you could do right now with their system.

**Offer to document.** Ask if the user wants to save this understanding for future sessions — a markdown file describing the system structure, key IDs, and how it's used. This pays off every time Claude works with the system later.

## Worked Example (demo workspace)

User asks: *"Explain my Task setup."*

1. **Discover** — `list_tags` on the workspace returns `#Task` (`demoTaskTag1`), `#Meeting` (`demoMeetTag1`), `#Person` (`demoPersTag1`), `#Decision`, `#PersonObservation`.
2. **Focus** — the user named Tasks, so no `AskUserQuestion` needed. Entry point: `demoTaskTag1`.
3. **Structure** — `get_tag_schema` on `demoTaskTag1` returns the fields: Assignee (`demoFldAsgn1`, instance of `#Person`, multi-value), Context (`demoFldCtx01`, multi-value), Urgency (`demoFldUrg01`, options: Critical / Fast-Track / Normal / Someday-Maybe), Due date (`demoFldDue01`), Parent Meeting (`demoFldPMtg1`, links back to a `#Meeting`).
   - `search_nodes` with `{"hasType": "demoTaskTag1"}` shows how many tasks exist and how often each field is actually filled.
   - You notice most tasks point back to a meeting via Parent Meeting — so Tasks are mostly born out of meetings.
4. **Document** — present the tag, its fields, and the meeting → task relationship as a small hierarchy.
5. **How I can help** — concrete offers, e.g.:
   - "List every open `#Task` assigned to Riya (`demoRiya0001`) with no due date."
   - "Show me Critical tasks in the Product context (`demoCtxProd1`)."
   - "After your next meeting, extract the action items and create properly-tagged `#Task` nodes for you."

## When to Ask the User

Use **AskUserQuestion** when:
- The focus isn't clear (always ask before exploring broadly).
- You find an unexpected pattern worth confirming.
- You're offering analysis options after documenting the structure.
- You're confirming before saving documentation.
