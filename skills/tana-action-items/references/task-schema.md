# Task Schema Reference

Field definitions for the `#Task` supertag, written against the shared demo workspace
([`demo-workspace/DEMO-WORKSPACE.md`](../../../demo-workspace/DEMO-WORKSPACE.md)). Every `demo…`
ID is a placeholder — replace it with your own (see
[`GETTING-STARTED.md`](../../../GETTING-STARTED.md) → "Finding your own IDs"). The **shape** here
mirrors a real Tana task setup; copy it and fill in your IDs.

## Task Supertag

- **Tag ID:** `demoTaskTag1`
- **Name:** Task

## Fields

### Assignee
- **Field ID:** `demoFldAsgn1`
- **Type:** Instance (references the `#Person` tag, `demoPersTag1`)
- **Multi-value:** Yes (a task can have multiple assignees)

### Context
- **Field ID:** `demoFldCtx01`
- **Type:** Instance (references a `#Context` tag)
- **Multi-value:** Yes

### Urgency
- **Field ID:** `demoFldUrg01`
- **Type:** Options (single select)
- **Options:**
  | Level | Option ID | Use When |
  |-------|-----------|----------|
  | 1. Critical | `demoUrgCrit1` | Blocking others, immediate action needed |
  | 2. Fast-Track | `demoUrgFast1` | High priority, this week |
  | 3. Normal | `demoUrgNorm1` | Standard priority (default) |
  | 4. Someday/Maybe | `demoUrgSome1` | Backlog, no deadline |

### Due date
- **Field ID:** `demoFldDue01`
- **Type:** Date
- **Format:** ISO date string (YYYY-MM-DD)
- **Usage:** Selective — only set when a real external constraint exists
  - YES: event dates, external commitments, explicit deadlines from others
  - NO: self-imposed goals, vague timing, internal prioritization (use Urgency instead)

### Parent Meeting
- **Field ID:** `demoFldPMtg1`
- **Type:** Instance (references the `#Meeting` tag, `demoMeetTag1`)
- **The canonical link back to the meeting.** Future meeting-prep finds prior open tasks by this
  field (+ Context), never by physical node location — so set it on every task.

### (Optional) Project / Charter
- **Field ID:** define your own (e.g. `demoFldProj1`)
- **Type:** Options or Instance
- A top-level initiative/theme you group delivery work under. The demo uses generic values like
  **Product Launch** and **Q3 Growth**. Tag sparingly — only delivery tasks that produce an output
  you'd want on a progress report (see SKILL.md Phase 3).

### (Optional) Task status
- Many setups leave status implicit (a task is "open" until checked off, "done" when checked).
  If you keep an explicit status field, add its ID and option IDs here. It's typically NOT set on
  creation — new tasks default to Active/open.

---

## Key People (your regular meeting attendees)

Populate this with **your own** people and their Person-node IDs. The demo workspace uses three
recurring collaborators plus you:

| Name | Node ID | Notes |
|------|---------|-------|
| You | `demoYou00000` | Default assignee for your own action items |
| Riya Sharma | `demoRiya0001` | Your direct report — most delegated tasks land here |
| Tom Becker | `demoTom00002` | A cross-functional peer — joint owner on shared work |
| Maya Chen | `demoMaya0003` | Your manager — senior stakeholder in upward meetings |

**Disambiguation tip:** when two people share a first name, document the default here (e.g. "‘Sam’
with no surname → Sam Rivera, the senior one; only assign to Sam Patel when explicitly named or the
context is clearly their domain"). The matching algorithm in SKILL.md Phase 3 relies on a documented
default to resolve bare first names.

---

## Key Contexts

Populate with **your own** Context-instance node IDs. The demo workspace splits work into three:

| Context | Node ID |
|---------|---------|
| Product | `demoCtxProd1` |
| Sales | `demoCtxSales` |
| Hiring | `demoCtxHire1` |

---

## Tana Paste Template

```
- [Task description] #[[^demoTaskTag1]]
  - [[^demoFldAsgn1]]:: [[^{personId}]]
  - [[^demoFldCtx01]]:: [[^{contextId}]]
  - [[^demoFldUrg01]]:: [[^{urgencyOptionId}]]
  - [[^demoFldPMtg1]]:: [[^{meetingId}]]
  - [[^demoFldDue01]]:: [[date:{YYYY-MM-DD}]]
```

---

## Notes

- Always fetch fresh IDs via `get_tag_schema` and `search_nodes` at the start of a session — IDs are
  stable, but your Person and Context lists grow over time, so search dynamically.
- Multi-value fields (Assignee, Context): never repeat a field-ID line in one Tana Paste block — it
  creates duplicate tuples. Import the first value, then add the rest into the tuple (SKILL.md Phase 5).
