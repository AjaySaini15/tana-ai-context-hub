---
name: tana-action-items
description: This skill should be used when the user asks to "process action items", "convert action items to tasks", "create tasks from meeting notes", "extract tasks from notes", "turn action items into tasks", "process [meeting name] meeting", "process the [meeting name] meeting from today", "please process [meeting name]", "process today's meetings", "process all meetings", "batch process meetings", "process meetings from today", "process meetings from yesterday", or shares unprocessed meeting notes with action items that need to be structured with assignees, contexts, and urgency levels.
argument-hint: "[meeting name, date, or paste action items]"
---

# Skill: Tana Action Items Processor

Convert raw meeting action items into structured Tana Tasks. Works for a single named meeting or a batch of today's meetings. Preserve full task descriptions — never shorten. Scan the entire meeting summary for implicit tasks, not just the Action Items section.

> **All examples use the shared demo workspace** ([`demo-workspace/DEMO-WORKSPACE.md`](../../demo-workspace/DEMO-WORKSPACE.md)):
> people **Riya Sharma** (`demoRiya0001`, your direct report), **Tom Becker** (`demoTom00002`, a peer),
> **Maya Chen** (`demoMaya0003`, your manager), and **you** (`demoYou00000`); a `#Task` tag (`demoTaskTag1`),
> `#Meeting` (`demoMeetTag1`), `#Decision` (`demoDecTag01`), `#PersonObservation` (`demoObsTag01`); and
> Context values **Product** (`demoCtxProd1`), **Sales** (`demoCtxSales`), **Hiring** (`demoCtxHire1`).
> Every `demo…` ID is a placeholder — swap in your own. See
> [`GETTING-STARTED.md`](../../GETTING-STARTED.md) → "Finding your own IDs".

> **Tana bridge:** the commands below assume a small CLI at `scripts/tana_query.py` that talks to your
> local Tana app, plus a `scripts/dedup.py` search helper. This repo ships placeholders — wire your own
> (see [`GETTING-STARTED.md`](../../GETTING-STARTED.md)). Anywhere you see `tana_query.py <cmd>` you can
> substitute the equivalent Tana MCP tool call (`get_tag_schema`, `search_nodes`, `read_node`,
> `import_tana_paste`, `set_field_content`, `check_node`, etc.).

---

## Phase 0: Read Daily Prep (optional, FIRST if you keep one)

If you maintain a per-day planning node (a "Daily Prep" — see the optional `day-prep` pattern), find today's node on today's calendar node before processing. Note: morning intention, the development area to watch, the target meeting, the priority of the day. These guide the evening reflection written in Phase 8. **If you don't keep a Daily Prep, skip this phase and Phase 8 entirely.**

**Finding the Daily Prep node — CRITICAL when one exists:**
1. `tana_query.py calendar today` → returns the **day node** (tagged `#Day`, e.g. "Today, Mon, 11 May")
2. `tana_query.py get-node <dayNodeId>` → shows children. Find the child rendered with your Daily-Prep tag.
3. The Daily Prep node is a **CHILD** of the day node. It is **NOT** the day node itself. Both may display "Today" in their name — do NOT confuse them. The day node is tagged `#Day`; the Daily-Prep child carries your planning tag.
4. **NEVER write fields to the day node.** Writing `set_field_content` to the day node creates orphan tuple nodes that appear as children of the day node but are invisible to the planning-tag schema. This is the most common Phase 8 failure mode.
5. **NEVER use a plain content child** (e.g. a node literally named "Day Prep — YYYY-MM-DD") for field writes — that's a content node inside the Daily Prep, not the tagged node.
6. **Verification:** After identifying the Daily Prep node ID, run `tana_query.py get-children <dailyPrepNodeId>` and confirm you see tuples for its field attrDefs. If you see meetings and content nodes instead of tuples, you have the wrong node (likely the day node).

Store the verified Daily Prep node ID for use in Phase 7 and Phase 8.

**Batch mode** — when invoked without a specific meeting (e.g., "process today's meetings", "process all meetings"):
1. Search today's calendar for all meeting-summary nodes not yet processed (no `#Task` children directly under the summary node).
2. Present the list: "Found N unprocessed meetings today: [list]. Process all or specific ones?"
3. Maintain a **Session Registry** — a running list of task titles + node IDs created this run. Before importing any task, check the registry first. If a title matches an already-created task, link to the existing node instead of creating a duplicate. This handles same-topic tasks surfacing across multiple meetings in one batch without extra Tana calls.
4. Process in chronological order. Present a combined task table grouped by meeting before asking for confirmation.

---

## Process Overview

### Phase 1: Gather Reference Data & Meeting Content

1. `get_tag_schema` on your Task supertag — field IDs and option values
2. Search your Context tag instances — valid context options
3. Search Person nodes — meeting attendees + common assignees
4. Get parent meeting node ID; check the meeting's Context field — this often determines task context (e.g. a partnership-outreach meeting may produce Sales tasks even though it touches a Product topic)
5. Meeting content — `read_node(meetingId, depth:1)` for Attendees + Context fields only. Then `get_children(meetingId)` → check for children in order:
   - If a child named **"Summary"** exists (plain container) → `tana_query.py read-deep <summaryContainerNodeId> 7` — preferred; returns the summary topics tree AND all sibling sections (Strategic Alignment, Participant Intelligence, Next Steps) in one call
   - Else if a child tagged with your meeting-summary tag exists directly under the meeting → `tana_query.py read-deep <meetingSummaryNodeId> 7` — fallback; may miss sibling sections if they weren't nested under the tag
   - Else: meeting not yet processed — stop

   Do NOT use `get-node` (depth:2 — truncates content). Do NOT read `meetingId` at depth — it has the raw transcript as a child. Skip nodes named "(End of notes)".
6. Prior meetings (optional) — search for previous meetings with the same title or attendees if strategic context is unclear. Action items often serve objectives not obvious from the current meeting alone.

### Phase 2: Gather Action Items

Read from three sources:

- **Source 1 (Tasks field)** — surfaced by a shallow meeting read; use only if the summary seems sparse
- **Source 2 (Action Items section)** — AI-processed, clean but may miss items
- **Source 3 (Full summary)** — Scan all sections: Key outcomes, Decisions, Next Steps, Blockers, Discussion points for implicit tasks buried in decisions and agreements.

Consolidate: deduplicate across sources, merge context, surface implicit tasks from decisions not listed in Action Items.

For each task: extract a full self-explanatory description, identify assignee, context, urgency. Include ALL attendees — create tasks for both internal and external assignees.

**Pre-dedup with agenda reference tasks (if you use a pre-built agenda):** Before running `dedup.py`, check each new task against any `Open:` items collected from the meeting's Agenda field (Phase 2.5 Source A below). If a new task semantically matches an `Open:` item that carries a `^[nodeId]`, immediately mark it as "Existing (ref)" with that node ID — no `dedup.py` call needed for that task. This is the fastest dedup path: the agenda already knows which tasks were expected to come up.

### Phase 2.5: Identify Tasks to Close + Triage Stale

*This phase assumes a meeting-prep step pre-populated the Agenda field with open prior tasks. If you don't pre-build agendas, skip Source A and rely on Source B + `dedup.py`.*

When used, the Agenda field is pre-populated with three structured sections, each carrying `^[taskNodeId]` suffixes pointing at the live Tana task:

- **`Open:` lines** inside strategy items — live open tasks expected to come up
- **`ALSO RAISE:`** — residual items mentioned but not woven into strategy
- **`STALE (60+ days — triage):`** — old open tasks that need close / reassign / keep decision

These IDs are the contract — they exist precisely so this phase can detect closure without re-searching Tana. **If the agenda contains no `^[taskNodeId]` references**, it predates this format; fall back to `dedup.py` for matching.

**Source A — Parse the agenda field:**

Read the Agenda field from the meeting node. Extract every `^[taskNodeId]` reference, categorising by section:
- IDs from `Open:` lines → **Live** bucket
- IDs from `ALSO RAISE:` lines → **Live** bucket (treat same as Open for closure detection)
- IDs from `STALE` block → **Stale** bucket (different downstream UX — see below)

For any agenda line without an `^[taskNodeId]` (legacy agenda or manually-added item): run `dedup.py` to find a match — same call pattern as Phase 2 dedup.

**Source B — Meeting Summary completion signals:**

Scan the summary for completion signals: "done", "resolved", fulfilled commitments ("Tom shared the deck"), decisions that retire a task ("we've decided not to pursue X"). Also explicitly check any "Completed / Closed" section of the summary if present.

For each completion signal:
1. First, try to match against IDs in the **Live** bucket (Source A) by title — if a signal describes a known agenda task, that's the strongest closure indicator.
2. If no match in Live bucket, run `dedup.py` to find a Tana task by text:
   ```bash
   python3 scripts/dedup.py \
     --tasks "T1: [what was completed — full description]|T2: [what was completed]" \
     --context <contextNodeId>
   ```
   MATCH = closure candidate from an out-of-agenda task.

**Present three categorised lists for review:**

```
CLOSURE CANDIDATES (Open agenda items with completion signals in summary):
  # | Task | Owner | Task ID | Evidence
  C1 | [title from agenda] | [owner] | demoTask0001 | Summary: "Tom shared the deck on Tuesday"
  C2 | [title] | [owner] | demoTask0002 | Decision retired this — "we're not pursuing X"

STILL OPEN (Open agenda items with no closure signal):
  • [title] — [owner] — ^demoTask0003

SUMMARY-ONLY MATCHES (completion signals matched via dedup, not on agenda):
  S1 | [matched task title] | [owner] | demoTask0004 | Signal: "[quote]"

STALE TRIAGE (60+ day items from agenda — pick action per item):
  T1 | [title] | [owner] | demoTask0005 | Age: 87 days
  T2 | [title] | [owner] | demoTask0006 | Age: 102 days
```

Ask:
- "Closure candidates (C# + S#) — which should I close?"
- "Stale items (T#) — for each: close / reassign to [new owner] / keep open with fresh date?"

For confirmed closures (C# and S#): `check_node` on the task node ID.

For stale-item decisions:
- **close** → `check_node`
- **reassign** → update the Assignee field via `set_field_content` mode replace, then leave open
- **keep with fresh date** → update the Due date field and optionally append a note to the task

Never auto-close or auto-reassign without user review.

### Phase 2.6: Person Intelligence Extraction — REQUIRED, do not skip

**This phase has two mandatory sub-steps: (A) individual observations, (B) relationship dynamics. Both must complete before moving to Phase 3.**

**IMPORTANT — ignore any AI "Participant Intelligence" section the summarizer wrote.** That section is often empty or says "Attendees not provided." Do not use its presence or absence as a gate. Generate observations yourself from the full summary content.

**Step A — Individual observations**

Read the Attendees field from the meeting node to get the roster. For each named attendee, scan the full summary for observations worth capturing. Threshold: specific, evidenced, adds something new — not routine job-function behavior. Target 1–3 observations per person per meeting.

The demo `#PersonObservation` schema (tag `demoObsTag01`):

| Field | Demo ID |
|---|---|
| Person (instance of #Person) | `demoFldOPrsn` |
| Type (options) | `demoFldOType` |
| Date | `demoFldODate` |
| Observation (text) | `demoFldOText` |
| Quote (text) | `demoFldOQuot` |

**Five observation types:**

| Type | Demo Option ID | Signal |
|---|---|---|
| **Position** | `demoObsPos01` | Argued for a view on a contested question; defended it against challenge |
| **Behavioral Pattern** | `demoObsBeh01` | Recurring mode: deflection, over-agreeing, anchoring first, probing before solutioning |
| **Desire** | `demoObsDes01` | What they're pushing toward — aspiration, resource ask, path they want |
| **Concern** | `demoObsCon01` | What they're resisting or worried about — pushback, hesitation, expressed risk |
| **Strength** | `demoObsStr01` | Notable capability shown — sharp insight, data command, facilitation quality |

**Tana Paste — import each observation under its Person node:**
```
- [Observation topic] #[[^demoObsTag01]]
  - [[^demoFldOPrsn]]:: [[^PersonNodeId]]
  - [[^demoFldOType]]:: [[^TypeOptionId]]
  - [[^demoFldODate]]:: [date]
  - [[^demoFldOText]]:: [Observation — specific and evidenced]
  - [[^demoFldOQuot]]:: [Quote or specific moment]
```

> **Optional — self-observations into a personality profile.** If one of the attendees is *you* (`demoYou00000`) and you keep a running self-profile document, you can additionally route your own observations there (e.g. a section for Cognitive Style, Values, Positions, Character) — surfaced as: "Personality signal: [section] — [what this moment reveals]". This is an optional personal-knowledge habit, not part of the core method.

**Present all observations for review before writing to Tana.** After generating observations (Step A) and relationship dynamics (Step B), present them grouped by person:

```
**[Person] -- [Type]:** [Observation summary]
> "[Quote]"

Relationship dynamics: [summary or "No relationship dynamics surfaced."]
```

Ask: "Good to import? Any edits?"

After confirmation, import PersonObservation nodes under each Person node. Do not skip the Tana write after approval — context pressure is not a valid reason to skip. Import in batches if needed.

**Step B — Relationship dynamics (mandatory, separate from observations)**

After generating individual observations, explicitly scan the summary for signals between two named participants:
- **Tension** — disagreement, pushback, competing interests, one person correcting another
- **Coalition** — two people aligned against a third view or direction
- **Bypass** — one person going around another in the hierarchy
- **Collaboration** — joint ownership of a deliverable or problem

For each signal found: if you keep a `#Relationship` tag, check for an existing relationship node for that pair. If it exists, update its Dynamic field. If not, create a new node. (A `#Relationship` tag is optional — if you don't keep one, just note the dynamic in the review and skip the write.)

**If no relationship signals exist in the meeting, state explicitly: "No relationship dynamics surfaced."** Do not silently skip.

Example `#Relationship` shape (define your own tag + field IDs — these are illustrative placeholders):
```
- [Person A name]↔[Person B name] #[[^<your-relationship-tag-id>]]
  - <person-A-field>:: [[^personANodeId]]
  - <person-B-field>:: [[^personBNodeId]]
  - <type-field>:: [[^typeOptionId]]
  - <dynamic-field>:: [Dynamic description — what was observed]
  - <date-field>:: [[date:YYYY-MM-DD]]
  - <source-field>:: [[^meetingSummaryNodeId]]
```
Suggested Type values: Tension · Coalition · Collaboration · Bypass · Mentor-Mentee. Suggested Status values: Active · Watch · Resolved.

### Phase 3: Match to Tana Entities

**Assignee** — Algorithm:

1. **Exact name match** against Meeting Attendees, then your canonical Person directory (see `references/task-schema.md` "Key People" section, which you populate with your own people).
2. **Delegation rule** — execution/operational work goes to the function owner (the person who runs that area / a sub-lead), NOT to you by default. Assign to yourself only when: you personally must act, only you can decide/evaluate, or it's external accountability where you are the named party.
3. **Disambiguation** — when two people share a first name, resolve by context (and document the default in `task-schema.md`). Example pattern: "Sam" with no surname defaults to the senior Sam unless the context is clearly the other Sam's domain.
4. **Surface ⚠** in the review table when a task auto-assigns to you AND a meeting attendee has clear function ownership for that work type. Let the user confirm or override.
5. **Fallback** — plain text name if no Person node match (the user can tag with #Person later).

**Context** — Semantic keyword match to existing Context instances. If unclear: present the top 2-3 options.

**Charter / Project (optional)** — a "Charter" is just a top-level initiative or theme you group work under (the demo uses generic values like **"Product Launch"** and **"Q3 Growth"** — replace with your own). Assign based on the type of work, not just the meeting's domain.

**The test:** "Does completing this task produce an output I'd want to see on a project/initiative progress report?" If yes → tag. If it's logistics, setup, or coordination → skip.

Two types of tasks within any initiative:

**Delivery tasks → tag the project.** These produce a specific output that advances the initiative.
- Data or analysis that feeds a strategic decision (opportunity lists, demand maps, utilization reports)
- Audit or tracking mechanisms that measure the initiative's KPIs
- Pilots, trials, or new processes being launched
- Reviews, assessments, or capability work you're owning independently

**Maintenance/admin tasks → no project tag.** These exist regardless of initiative. Most tasks in a meeting are operational — project tagging should be the exception, not the default. Expect 2-4 project-tagged tasks per meeting at most.
- Pure scheduling / calendar logistics (book a slot, fix a meeting time, send an invite)
- Access requests, ticket closures, IT setup
- One-off data shares with no analysis (forward a file, share a list)
- CRM cleanup, duplicate removal, status field updates
- Onboarding form circulation, migration plans, tech stability fixes
- Hiring and team restructuring (unless the hire IS the initiative's deliverable)
- Process fixes, payout/backlog clearing (process fixes, not strategic outputs)
- Data requests from other teams

**Task belongs to a different project than the meeting's primary domain** → tag the correct project, not the meeting's.

If you keep a Charter/Project field on Task, set it the same way as any options/instance field. Define your own field ID and values; the demo's generic illustration is a `Project` field with values like "Product Launch" and "Q3 Growth".

**Urgency:**

Evaluate using two passes: (1) set base tier from the strongest signal, (2) apply upgrade modifiers.

**Base tier — first match wins:**

| Signal | Level |
|---|---|
| Literal "urgent"/"ASAP"/"immediately" in transcript | Critical |
| A senior stakeholder explicitly stated as waiting or blocked RIGHT NOW | Critical |
| Deadline is TODAY (same calendar day as the meeting) | Critical |
| Something currently broken/failing causing operational damage now | Critical |
| Strategically foundational new system/metric being built from scratch — the meeting's central structural deliverable that downstream work depends on | Critical |
| Explicit deadline < 3 days, or "before [named event] tomorrow/this week" | Fast-Track |
| Task is blocking a senior stakeholder (they cannot proceed without it) | Fast-Track minimum |
| Task is a blocker for another person or downstream task (see Blocking annotation below) | Fast-Track minimum |
| Recurring review-cycle follow-up and next occurrence < 3 days away | Fast-Track |
| New pilot / test requiring validation (time-sensitive data) | Fast-Track |
| Standard task, clear owner and timeline implied | Normal |
| Exploratory/investigative: "explore", "think about", "consider", "look into", "worth trying", "nice to have", "eventually", "next quarter", "when bandwidth", "no rush", "at some point" | Someday/Maybe |
| Task has no assignee, no deadline, no urgency signal, and is purely investigative | Someday/Maybe |
| Purely administrative with no external dependency (filing, archiving, background cleanup) | Someday/Maybe |

**Upgrade modifiers (apply after base tier):**
- You are doing something FOR a senior stakeholder (e.g. your manager) or waiting ON them to unblock work → Fast-Track minimum. Does NOT apply when they are merely mentioned or informed.
- Team task assigned to a direct report with a stated or implied cycle deadline → Fast-Track if < 3 days
- Task moves a high-weight KPI for the assignee → Fast-Track minimum (if you track per-person KPI weights)

**Blocking annotation — do this before setting urgency:**

Before assigning urgency, check whether the task is blocking another person or process. Blocking signals:
- Meeting notes explicitly say someone is waiting: "X is waiting on you to send Y", "we can't proceed until Z is confirmed"
- Task description involves a gate action: "confirm with X so [plan] can proceed", "get approval from X", "sign off on", "circulate to team before [event]"
- Task is the stated input to another task in the same meeting

If blocking is detected:
1. Append **(blocks: [who/what])** to the task title — e.g., "Confirm with your manager: who owns the next review **(blocks: review ownership planning)**"
2. Set urgency to Fast-Track minimum (upgrade to Critical if the blocked party is senior or the blockage is time-sensitive)

The `(blocks:` annotation serves two purposes: it upgrades urgency at creation, and it gives a downstream prioritization step a reliable signal when scoring tasks later.

**Due dates** — Only for real external constraints (event dates, external deadlines, stakeholder commitments). Skip vague timing — Urgency handles prioritization. **Team tasks MUST have a due date** — if not stated, infer from context (weekly-review cycle → end of week). Your own tasks: due date optional.

**Due date active check:** Before presenting the review table, flag any team task with no due date and show a suggested date (inferred from the meeting cycle or urgency). The user confirms or overrides. Do not silently leave team tasks without due dates.

**Ambiguity** — Missing assignee: present the attendee list as options. Conflicting signals: an explicit keyword beats absence of info.

### Phase 4: Generate Structured Tasks

**Single-assignee / single-context (default):**
```
- Task description #[[^demoTaskTag1]]
  - [[^demoFldAsgn1]]:: [[^PersonNodeId]]
  - [[^demoFldCtx01]]:: [[^ContextNodeId]]
  - [[^demoFldUrg01]]:: [[^UrgencyOptionId]]
  - [[^demoFldPMtg1]]:: [[^MeetingNodeId]]
```
(Add a Project/Charter field line only when the project is clear.)

**Multi-value fields (Assignee, Context) — NEVER repeat the same field ID twice in Tana Paste.** Repeating a field line (e.g., two `[[^demoFldAsgn1]]::` lines) creates duplicate tuples instead of a single multi-value field. Use the two-step approach:

1. Import the task with the **first** assignee/context only (template above)
2. After import, add remaining values via the tuple approach (see Phase 5 below)

### Phase 5: Consolidated Review & Import

**Master rule: ONE consolidated review covering every proposed write before any Tana operation.** Splitting into separate gates (tasks → import → ask about observations → ask about decisions) causes rework — it's easy to import a batch of tasks and then have to roll back when closure candidates were missed in the agenda walk.

Present the consolidated review with ALL Tana node IDs visible BEFORE any write:

```
═══════ PROPOSED WRITES FOR <Meeting Name> ═══════

NEW TASKS (N)
# | Task | Assignee (NodeId) | Context | Urgency | Project | Due | Source

CLOSURE CANDIDATES (N) — from agenda Open: items + summary signals
# | Existing task title | Task ID | Owner | Evidence

STALE TRIAGE (N) — 60+ days, pick action per item
# | Title | Task ID | Age | Action: close / reassign-to / keep-with-date

PERSON OBSERVATIONS (N)
• Person (NodeId) | Type | Observation | Quote

RELATIONSHIP DYNAMICS (N)
• Person A ↔ Person B (NodeIds) | Type | Dynamic

DECISIONS (N)
# | Decision | Context | Project

═══════════════════════════════════════════════════
```

Mark uncertain assignees with ⚠ in the Assignee column. Source types: **Tasks** (field), **Action Items** (summary section), **Tasks + Summary** (consolidated), **Gap** (implicit from decisions/discussions — not in original action items), **Existing (ref)** (already in Tana — reference only, no new task).

Ask single confirmation: **"Approve all? Adjust any line? Drop any item?"**

After confirmation, execute writes in this sequence (all imports run inline via `import_tana_paste` / `tana_query.py import` — never stage tana-paste content in a temp file first):
1. New tasks → import under the meeting node. Placement (meeting root vs its Summary) is NOT load-bearing — the **Parent Meeting field (`demoFldPMtg1`) is the canonical link and MUST be set on every task**. Future agenda-building finds prior open tasks by this field + by Context, never by physical location.
2. Closures → `check_node` on confirmed task IDs
3. Stale triage actions → `check_node` (close) / `set_field_content` Assignee (reassign) / `set_field_content` Due date (keep with fresh date)
4. PersonObservations → import under each Person node
5. Relationship dynamics → create or update `#Relationship` nodes (if you keep them)
6. Decisions → import into your Decision Log (`demoDecLog001`)
7. Stale Tasks-field cleanup → trash the plain summarizer text the Tana AI auto-populated into the meeting's Tasks field, now superseded by the tagged `#Task` nodes (detail below)

For tasks already in Tana: `[[^existingTaskNodeId]]` reference only — no new task created.

**Stale Tasks-field cleanup:** The Tana AI summarizer often auto-fills the meeting node's Tasks field (the tuple whose field-definition child is named "Tasks") with plain-text action items. Once the canonical `#Task` nodes exist these are redundant and mismatch the real list — especially after the user drops or reframes items in review. `get_children` on the meeting node → find the Tasks-field tuple → trash every **untagged plain content value node** under it. NEVER trash the field-definition node (named "Tasks"), and NEVER trash a properly-tagged `#Task` node. Tana leaves one blank placeholder value when the field is emptied — that is normal; do not keep trashing it. Skip if the field is empty.

**Parent Meeting invariant (mandatory post-import check):** After creating tasks, confirm **every** new `#Task` has the Parent Meeting field (`demoFldPMtg1`) set to the meeting node — this is the link that surfaces the task in future prep. Any task missing it is invisible to the next agenda. Fix any that are unset via `set_field_content` before finishing.

**Multi-value field post-import (Assignee, Context):** For any task with multiple assignees or multiple contexts, after the initial `import_tana_paste`:
1. `get_children` on the newly created task node
2. Find the relevant tuple — the child with `docType: "tuple"` whose children include the field's `attrDef` ID (`demoFldAsgn1` for Assignee, `demoFldCtx01` for Context)
3. `import_tana_paste` into that tuple node with additional values:
   ```
   - [[^person2NodeId]]
   ```
   (or `- [[^context2NodeId]]` for Context)

This applies to ALL multi-value instance fields. Never repeat a field ID line in Tana Paste — it creates duplicate tuples.

**Dedup is text-only:** Dedup searches by task text keywords, not by assignee. Changing an assignee in the review table does NOT require re-running dedup.

### Phase 5c: Extract Decisions

After importing tasks, scan the meeting summary for decisions.

**Step 1 — Extract and review decisions**

Source: "Decisions made" bullets within each topic section, plus any explicit agreement statements ("we decided", "going forward", "the rule is", "we've agreed").

**NOT decisions (filter out):**
- AI recommendations or analyst suggestions ("you could consider X", "one option is Y")
- Proposals that didn't land — discussed but no commitment ("we should think about X")
- Open questions or items left for follow-up
- Status updates ("X is done", "Y is pending") — these are facts, not decisions

A decision requires: **stated outcome + commitment to act, not act, or change a rule.**

Filter: meaningful decisions only — same bar as project tagging. Skip logistics, scheduling, access requests.

For each qualifying decision, determine: decision text (self-explanatory without the meeting), Context, and Project (only if clearly tied to one).

Present a review table before importing:

| # | Decision | Context | Project |
|---|----------|---------|---------|
| 1 | [Decision text] | Product | Product Launch |
| 2 | [Decision text] | Sales | — |

Ask: "Import decisions? Adjust context or project?"

**Step 2 — Import decisions**

After confirmation, for each decision create a `#Decision` node under your Decision Log (`demoDecLog001`):

```
%%tana%%
- [Decision title — what was decided, self-explanatory] #[[^demoDecTag01]]
  - [[^demoFldOutc1]]:: [Full decision text — enough context to understand without the meeting]
  - [[^demoFldDCtx1]]:: [[^contextNodeId]]
```

Set the date field after import:
```bash
python3 scripts/tana_query.py set-field <decisionNodeId> demoFldDDate "YYYY-MM-DD"
```

> **Optional — link to a long-running problem.** If you keep "strategic problem" nodes (persistent challenges that accumulate decisions over time), append a reference under the relevant problem node so the decision shows up in its children:
> ```bash
> python3 scripts/tana_query.py import <problemNodeId> "- [[^<decisionNodeId>]]"
> ```
> Choose ONE primary problem as the home (where the decision node lives); reference it under any secondary problems. Edit-once, propagate-everywhere — if the source decision is trashed, references break, so pick the home carefully.

**`#Decision` tag schema (demo):**
- Tag ID: `demoDecTag01`
- Outcome field: `demoFldOutc1`
- Date field: `demoFldDDate`
- Context field: `demoFldDCtx1`
- Container (Decision Log): `demoDecLog001`

---

### Phase 6: Generate MoM (Minutes of Meeting) email

Generate a formatted HTML MoM email using the template at `references/mom-email-template.html`.

**Steps:**
1. Read the template file
2. Fill in all `[BRACKETED]` placeholders with actual meeting content, in this order:
   - Decisions made: what was agreed and why
   - Action items: flat list with 3 columns (Who | What | By when). Alternate row backgrounds via inline styles (the template shows the exact colors).
   - Key discussion points: **nested bullet structure** — each topic as a top-level bullet, sub-bullets for key facts/data/outcomes. No paragraph prose. All detail preserved, just broken into scannable points.
   - Open items / blockers: delete the section if none
   - Next steps: next review date, follow-up meeting, pre-reads needed
3. Save the filled HTML somewhere durable (e.g. `output/MoM - [Meeting Name] - [Date].html`).
4. **(Optional) Create an email draft** — if you have an email bridge (an SMTP/Gmail/API helper), resolve attendee emails from each Person node's Email field, then create a draft addressed to them. Tell the user where the draft landed. If you have no email bridge, just hand back the saved HTML file path.
5. **(Optional) Open the saved file** in a browser for preview, and print the subject line: `**Subject:** MoM — [Meeting Name] | [Date]`

**Content rules:** Keep everything tight and scannable.
- **Decisions:** bullet list, one line each — include owner inline if clear
- **Action items:** grouped by assignee (bold name label → tasks below). One line per task. Alternating row shading via inline styles. Due date bold, right-aligned.
- **Key Points:** 1-2 lines per topic max; lead with the insight or data point, not background. No nested sub-bullets unless a topic genuinely has 3+ distinct facts worth calling out.
- **Open items:** one line — blocker + owner + resolution trigger
- Use plain names for assignees (not @Name) — this is an email, not a chat app.

### Phase 7: Strategic Progress Check (optional)

*Skip this phase if you don't track initiatives/charters.* If you do: review the meeting against your initiatives. Only surface initiatives with actual relevance — skip entirely if there's no movement. Also check: relationship-building opportunities with senior stakeholders, large wins or saves discussed, team-capability improvements — these are non-obvious signals worth capturing.

```
Strategic Alignment:
- [Project/Initiative]: [brief note, or — if none]
```

If an initiative moved and you keep a Daily Prep node, record it in that node's "progress" field via `set_field_content` with `mode="append"`:
```
set_field_content(nodeId=dailyPrepNodeId, attributeId="<your-progress-field-id>", content="[Meeting name] ([Project]): [note]", mode="append")
```
Use `set_field_content` for existing nodes — NOT `import_tana_paste` with field syntax (see your Tana write-rules). `mode: "append"` handles merging — no need to read first.

### Phase 8: Daily Prep Evening Reflection (optional)

*Only if you keep a Daily Prep node and a self-coaching habit. Otherwise skip.* Run inline — don't defer.

1. Use the Daily Prep node ID stored in Phase 0. **Do NOT re-derive it from the calendar node here.** If Phase 0 was skipped, re-run its identification steps to find the planning-tag child of the day node.

**GUARD:** Before writing, verify `dailyPrepNodeId` ≠ the day node ID. If they match, STOP — you have the wrong node. Go back and find the planning-tag child.

The two illustrative sub-writes (a "soft-skills reflection" field and a "decision patterns" field) both use `set_field_content` with `mode="append"`, reading the existing value first only when you need to avoid duplicating a same-day entry. **NEVER use `import_tana_paste` with field syntax to write a field on an existing node** — it creates orphan tuples.

```
set_field_content(nodeId=dailyPrepNodeId, attributeId="<your-reflection-field-id>", content="[reflection text]", mode="append")
```

---

## Output Format

| # | Task | Assignee | Context | Urgency | Source |
|---|------|----------|---------|---------|--------|
| 1 | [Full task description] | Riya Sharma | Product | Fast-Track | Action Items |
| 2 | [Full task description] | ⚠ Tom Becker? | Sales | Normal | Gap (decisions) |
| 3 | [Full task description] | Riya Sharma | Product | Fast-Track | Existing (ref) — [Meeting, Date] |

Mark uncertain assignees with ⚠ in the Assignee column. Dedup is text-only — no re-run needed when an assignee is corrected.

Source types: **Tasks** (field), **Action Items** (summary section), **Tasks + Summary** (consolidated), **Gap** (implicit from decisions/discussions — not in original action items), **Existing (ref)** (already in Tana — reference only, no new task).

Then ask: "Ready to import? Adjust any before importing? (Correcting a ⚠ assignee will re-check for duplicates before importing that task.)"

---

## Deduplication

Dedup uses a two-step approach: `dedup.py` searches Tana and returns existing tasks as JSON, then Claude does the semantic comparison in-session. No subprocess LLM calls — all comparison happens in the main conversation.

### Step 1 — Run dedup.py to search Tana

`dedup.py` is a search-only helper. It extracts keywords from the new task descriptions, queries Tana by text match (no assignee filter), and returns a JSON array of existing tasks (id + name). Optional `--context` narrows the search to a domain. (Wire your own — it's a thin wrapper over a Tana text search; see [`GETTING-STARTED.md`](../../GETTING-STARTED.md).)

```bash
python3 scripts/dedup.py \
  --tasks "T1: full description|T2: full description|T3: full description" \
  --context <contextNodeId>   # optional — narrows to domain
```

Output: JSON array of existing tasks, e.g. `[{"id": "demoTask0001", "name": "Task title"}, ...]`
Empty result: `[]` — all tasks are new.

**Batching:** One call per context. Group tasks by their context, run one dedup call per group.

### Step 2 — Claude compares in-session

Read the JSON output and compare each new task description against the existing task names semantically:

- **MATCH** — same intent and action, regardless of wording → link the existing node, show as "Existing (ref)" in the review table
- **SIMILAR** — same broad topic but different scope or deliverable → create a new task AND flag "⚠ Possible duplicate: [existing task title]". Surface to the user.
- **NONE** — no match → new task, proceed to import

If `dedup.py` returns `[]` or errors: treat all tasks as NONE.

Never silently deduplicate — even MATCH verdicts are shown in the review table so the user can override.

---

## Reference Files

- `references/task-schema.md` — Task supertag field IDs and option values (populate with your own)
- `references/matching-rules.md` — Entity matching rules (assignee / context / urgency / due date)
- `references/meeting-summary-prompt.md` — a generic prompt to paste into Tana's built-in meeting-summary tool so summaries come out in the structure this skill expects
- [`demo-workspace/DEMO-WORKSPACE.md`](../../demo-workspace/DEMO-WORKSPACE.md) — the fictional workspace every example uses
- [`GETTING-STARTED.md`](../../GETTING-STARTED.md) — finding your own IDs, and wiring the Tana bridge (`tana_query.py` / `dedup.py`) and an optional email bridge

> **Before any Tana write,** know your tool's field-write rules — multi-value fields, tuple logic, and which destructive operations have no undo. Writing a field on an existing node uses `set_field_content`, never `import_tana_paste` with field syntax.

---

## Quick Reference: Tana Paste

```
- Task title #[[^demoTaskTag1]]
  - [[^demoFldAsgn1]]:: [[^personId]]
  - [[^demoFldCtx01]]:: [[^contextId]]
  - [[^demoFldUrg01]]:: [[^urgencyOptionId]]
  - [[^demoFldPMtg1]]:: [[^meetingId]]
  - [[^demoFldDue01]]:: [[date:YYYY-MM-DD]]          ← team tasks must have this
```

Urgency option IDs (demo): Critical `demoUrgCrit1` · Fast-Track `demoUrgFast1` · Normal `demoUrgNorm1` · Someday/Maybe `demoUrgSome1`.

**Multi-value fields (Assignee, Context): NEVER repeat a field ID line.** Two `[[^demoFldAsgn1]]::` lines = two broken tuples. Use a single value in Tana Paste, then post-import: `get_children` → find the tuple → `import_tana_paste` additional values into the tuple.

Assignee fallback (no Person node found): use a plain text name — the user can tag with #Person later.

All field IDs, urgency option IDs, context node IDs, assignee node IDs: `references/task-schema.md`.
