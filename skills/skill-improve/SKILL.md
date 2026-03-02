---
name: skill-improve
description: Capture in-session corrections and fold them back into skills permanently. Updates the skill in Tana and locally, increments version, appends to change log. Auto-triggers after skill corrections — run explicitly with /skill-improve [skill-name].
argument-hint: "[skill-name]"
---

# Skill: Skill Improve

The self-improvement loop. When a skill produces wrong output and the user corrects it, this skill captures that correction, proposes an exact update to the skill definition, and persists it — to the local SKILL.md AND the Tana node. Version increments. Change log grows.

Next session, the same mistake doesn't happen.

---

## Auto-Trigger Protocol

**After any skill runs and the user makes a correction, proactively offer to save the improvement.**

Watch for these patterns during a session:
- User says "No, [that/this] should..." after a skill produces output
- User says "Actually, ..." to override skill output
- User says "That's wrong, ..." and provides the correct output
- User corrects an attribution, a field assignment, a format, a missed item
- Any explicit correction of skill behavior (not just a one-off instruction)

When detected, say:

> "I noticed I got [specific thing] wrong in [skill-name]. Should I save this as a permanent improvement to the skill? It'll prevent the same issue in future sessions."

If user says yes: proceed to Phase 2 (skip Phase 1 — you already have the context).
If user says no: continue without saving.

**Do not offer auto-trigger** for:
- Corrections to conversational responses (not skill output)
- One-off exceptions the user explicitly says are situational ("just this time")
- Corrections to **data values** within the output — wrong number, wrong name, wrong date in the content. These are input errors, not skill failures. The test: would the same transcript run again produce the same wrong output? If yes, it's a skill issue. If no (the data was just wrong), it's not.
- Corrections to data (wrong meeting content) rather than skill behavior (wrong process)

---

## Phase 1: Identify the Skill and Correction

### When triggered explicitly: `/skill-improve [skill-name]`

1. **Confirm the skill name.** If argument provided, use it. If not, ask: "Which skill needs improving?"

2. **Find the skill** in this order:
   - Check `~/.claude/ai-memory/sync-manifest.json` for a node with matching name and `contextType: "skill"`
   - If found: read from Tana using `read_node` at depth 3 → this is the authoritative version
   - If not in manifest: check `~/.claude/skills/[skill-name]/SKILL.md` as fallback

3. **Ask what needs improving:**
   > "What went wrong? Describe the failure and what the correct behavior should be."

   Listen for:
   - A specific failure ("it assigned the task to the wrong person")
   - A missing behavior ("it never asks for confirmation before pushing")
   - An incorrect assumption ("it assumes all tasks go under the current meeting, but some should go under a context node")
   - A format problem ("the output table was missing the urgency column")

### When auto-triggered after a correction

Skip the above. The failure and correction are already known from the conversation context.

Summarize what you understood:
> "Got it — [skill-name] should [correct behavior] instead of [incorrect behavior]. Let me propose an update."

Ask user to confirm the summary is right before proceeding.

---

## Phase 2: Propose the Improvement

### Read the current skill

If not already loaded: read the full SKILL.md content from Tana node or local file.

### Generate a precise diff

Identify **exactly** which section of the skill needs to change. Show a before/after:

```
Proposed change to: tana-action-items

SECTION: Task Attribution Rules

BEFORE:
  When multiple people are mentioned, assign the task to the person
  who raised the action item, defaulting to the meeting organizer.

AFTER:
  When multiple people are mentioned, assign the task to the person
  explicitly given ownership ("X will do this", "X to follow up").
  If ownership is ambiguous, assign to the meeting organizer.
  NEVER default to the user running the skill as assignee.

REASON: Tasks were being assigned to Ajay when Manmohan was the
action owner. The skill was defaulting to the session user instead
of reading the transcript for explicit ownership.
```

Keep the proposed change **surgical** — modify only what's needed. Don't rewrite sections that aren't broken.

### Ask for confirmation

> "Does this look right? I'll update the skill, bump the version, and log the change."

Options:
- Yes — proceed
- Adjust — user refines the proposed change, re-propose
- No — discard

---

## Phase 3: Apply the Improvement

### 3a. Determine new version number

Read the current version from the skill node (in Change Log section or Version field).
- Bug fix or behavior correction → increment patch: v1.2 → v1.3
- New capability or significant behavior change → increment minor: v1.2 → v1.3...
  actually use this rule:
  - Correction of wrong behavior: patch (v1.2 → v1.3)
  - New behavior added: minor (v1.2 → v2.0)
  - Major rewrite or new purpose: major (v1.x → v2.0)

### 3b. Update all tool paths

Read `manifest.skillPaths` to find every tool that has a local copy of this skill.

For each configured tool path:
- Read the existing local file for that tool
- Apply the equivalent of the diff — translate if needed (the core change is the same, but formatting may differ per tool)
- Write back

This means a correction made in Claude Code automatically propagates to the Gemini prompt file, the generic skills folder, and any other configured tool — no manual copy-paste.

### 3c. Update Tana node

If the skill has a Tana node (in manifest):

1. `get_children` on the skill node — find the "Skill Content" child section
2. Find the specific child node that contains the changed section
3. `edit_node` to update that specific node's content
4. **Append to Change Log** — `import_tana_paste` under the "Change Log" child:

```
%%tana%%
- [new_version] ([today's date]) — [one sentence: what changed]. Triggered by: [brief description of failure that prompted this].
```

5. If the skill has a "Version" field: `set_field_content` to update it
6. Set `Modified By` = `claude-code`, `Last Synced` = today

### 3d. Update manifest

Update the node's `lastSyncedLocal` to today.

---

## Phase 4: Confirm

Report to user:

```
Skill improved: tana-action-items

Version: v1.2 → v1.3
Change: Task attribution now reads for explicit ownership in transcript
        before defaulting to meeting organizer. Never defaults to
        session user as assignee.

Updated:
  ✓ ~/.claude/skills/tana-action-items/SKILL.md
  ✓ Tana node (change log updated)
  ✓ Sync manifest

This improvement will be available to any LLM that loads this skill
from Tana on the next session.
```

---

## Skill Node Structure in Tana

For reference — this is what a skill node looks like in Tana when properly set up:

```
[Skill Name] #AI_Context
  Context Type:: skill
  Priority Tier:: tier-2-important
  Modified By:: claude-code
  Last Synced:: [[date:YYYY-MM-DD]]
  Local File Path:: ~/.claude/skills/[skill-name]/SKILL.md

  Purpose
    [One paragraph: what this skill does and when to use it]

  Eval Criteria
    [What good output looks like]
    [Known failure modes this skill should NOT produce]
    [Invariants: things that must always be true in the output]

  Skill Content
    [The full SKILL.md instructions, section by section as child nodes]

  Change Log
    v1.3 (2026-03-01) — Fixed task attribution to read explicit ownership
                        before defaulting. Triggered by: wrong assignee in
                        Manmohan 1:1 processing.
    v1.2 (2026-02-27) — Added overexplaining count to soft skills check.
                        Triggered by: Manmohan baseline revealed missed pattern.
    v1.1 (2026-02-11) — Extended task extraction to full MoM, not just
                        action items section. Triggered by: missed 10 tasks
                        in Bangalore plan meeting.
    v1.0 (2026-02-06) — Initial version.
```

The Change Log is the proof that this system works. It's a record of every time the skill got smarter.

---

## Batch Improvement Mode

When called with `/skill-improve --all`:

1. List all skills in the manifest with `contextType: "skill"`
2. For each skill, read its node and show the current version + last change date
3. Ask: "Any of these need improvements right now?" with the list
4. User can say "Yes, [skill-name]: [description]" for multiple skills
5. Process each one sequentially

---

## Important Rules

- **Surgical edits only.** Never rewrite a whole skill to fix one thing. Find the exact section and change only that.
- **Change log is sacred.** Never delete or modify existing change log entries. Only append.
- **Version always increments.** Never push an update without bumping the version.
- **Reason is required.** Every change log entry must include what triggered the improvement — not just what changed, but why.
- **If the skill isn't in Tana yet:** after improving locally, ask "Should I add this skill to Tana so future improvements are tracked there?" and run the bootstrapping phase from ai-memory-setup if yes.
- **If Tana update fails:** still save locally, warn the user, and note that the Tana node needs a manual push.
