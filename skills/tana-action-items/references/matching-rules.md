# Entity Matching Rules

Detailed rules for matching raw action-item text to Tana entities. Examples use the shared demo
workspace ([`demo-workspace/DEMO-WORKSPACE.md`](../../../demo-workspace/DEMO-WORKSPACE.md)):
people **Riya** / **Tom** / **Maya** / **you**, and Contexts **Product** / **Sales** / **Hiring**.

---

## CRITICAL: Task Extraction Scope

**Never extract tasks only from the "Action Items" section.** Always read the FULL meeting summary including:
- Key points discussed
- Decisions made
- Metrics & observations
- Coaching / notes sections (may contain follow-up actions)
- "Decisions pending" sections
- Strategic alignment / missed opportunities

Tasks hide in Decisions sections, Key Points, and even side notes. Cross-reference all sections
against the Action Items list — anything actionable that's NOT already in Action Items should be
surfaced as an additional task. Extracting only from Action Items consistently misses 20–30% of real
tasks.

---

## Assignee Matching

### Detection Patterns

**Explicit assignment:**
- "[Name] to…" → Assignee is Name
- "[Name] will…" → Assignee is Name
- "Assigned to [Name]" → Assignee is Name
- "Owner: [Name]" → Assignee is Name

**Self-reference (speaker is assignee):**
- "I will…" → speaker is assignee (determine from meeting context)
- "I need to…" → speaker is assignee
- "My action…" → speaker is assignee

**Implicit from context:**
- Task mentioned during someone's update → likely their task
- Response to someone's question → the responder may own the follow-up

### Name Variations

Handle common variations:
- First name only: "Riya" → "Riya Sharma" (`demoRiya0001`)
- Nickname: check if you've documented nicknames in `task-schema.md`
- Case-insensitive matching

### Ambiguity Resolution

When the assignee is unclear:
1. Check if only one person is discussing the topic
2. Look for pronouns referencing a specific person
3. If still unclear, present options to the user:
   - List meeting attendees
   - Include an "Unassigned" option
   - Allow multiple assignees if collaborative

### Delegation Default

Operational/execution work goes to the **function owner** (the person who runs that area), not to
you by default. Assign to yourself only when you personally must act, only you can decide/evaluate,
or it's external accountability where you're the named party. When a task auto-assigns to you AND an
attendee clearly owns that work type, surface it with ⚠ for the user to confirm or override.

---

## Context Matching

### Keyword Mapping

Replace these illustrative rows with **your own** Context values and trigger keywords. The demo
workspace splits into Product / Sales / Hiring:

| Keywords | Likely Context |
|----------|----------------|
| roadmap, feature, release, spec, bug, UX | Product |
| revenue, pipeline, deals, pricing, prospect, renewal | Sales |
| hiring, recruiting, interview, candidate, headcount, onboarding | Hiring |

### Semantic Matching

Beyond keywords, understand intent:
- "Get the pricing one-pager out before the renewal call" → Sales
- "Cut scope on the import feature" → Product
- "Loop in the recruiter on the senior role" → Hiring

### Multiple Contexts

Some tasks span multiple contexts:
- Allow multi-value assignment
- Put the primary context first, then related contexts

### Default Behavior

If the meeting has a known context (e.g., a "Product" meeting):
- Default to the meeting's context for ambiguous tasks
- Only override when a task clearly belongs elsewhere

---

## Urgency Assessment

*(SKILL.md Phase 3 has the full two-pass rules — base tier + upgrade modifiers. This is the quick map.)*

### Explicit Signals (Highest Priority)

| Signal | Urgency |
|--------|---------|
| "urgent", "ASAP", "critical", "emergency" | 1. Critical |
| "high priority", "important", "priority" | 2. Fast-Track |
| "when you can", "low priority", "backlog" | 4. Someday/Maybe |

### Deadline-Based

| Deadline | Urgency |
|----------|---------|
| Today / Tomorrow | 1. Critical |
| This week / next few days | 2. Fast-Track |
| This month / next week | 3. Normal |
| No deadline / "eventually" | 4. Someday/Maybe |

### Dependency-Based

Tasks that block others should be elevated:
- "Blocking the release" → Critical
- "Need this before X can start" → Fast-Track
- Independent tasks → Normal

### Default

When no urgency signals are present:
- **Default to "3. Normal"**
- Don't over-prioritize — too many Critical tasks dilutes the meaning

---

## Due Date Extraction

### Explicit Dates
- "by January 15th" → `2026-01-15`
- "due 2/4" → `2026-02-04`
- "deadline: Feb 10" → `2026-02-10`

### Relative Dates
- "by end of week" → Friday of the current week
- "next Monday" → calculate the actual date
- "in 2 weeks" → current date + 14 days
- "by month end" → last day of the current month

### Implicit Dates
- For a recurring meeting's tasks → next meeting date
- Sprint-based → sprint end date

---

## Validation Rules

Before importing tasks, validate:

1. **Required fields present:**
   - Task description (non-empty)
   - Assignee (at least one, or flagged as unassigned)
   - Context (at least one)
   - Urgency (default to Normal if missing)

2. **Valid references:**
   - Person ID exists in the workspace
   - Context ID exists in the workspace
   - Urgency option ID is valid

3. **Sensible combinations:**
   - Critical urgency should have a near-term due date
   - Someday/Maybe shouldn't have an immediate deadline

---

## Edge Cases

### Team Tasks
- "We need to…" → may need a discussion on the owner
- Present as a collaborative task or ask for the primary owner

### Vague Tasks
- "Look into X" → ask for more specificity or import as-is (likely Someday/Maybe)
- May need a follow-up to refine

### Already Done
- "We already did X" → don't create a task; note as completed if a closure record matters

### Questions vs Tasks
- "Should we do X?" → not a task, but may become one
- Flag for the user: "Is this a task or still under discussion?"
