# Meeting Summary Prompt (for Tana's built-in summarizer)

Paste this into Tana's meeting-summary prompt field. It makes Tana's AI write summaries in the
**structure the `tana-action-items` skill expects** — so action items, decisions, participant notes,
and next steps land in predictable sections that the skill can parse.

It's generic on purpose. Two things to customize before you use it:
1. The **CONTEXT** block — a couple of lines about you and your work so the summarizer understands who's who.
2. The **GLOSSARY** — your own jargon/acronyms so the model expands them correctly. (Delete it if you have none.)

There are two versions below: a **full** prompt and a **minimal** copy-paste prompt. Use whichever
your summarizer handles best.

---

## Why the heading levels matter

Tana builds its node tree from Markdown heading levels. The skill reads the summary by walking that
tree, so keep the levels consistent:

- Use `###` for the **meeting title only**.
- Use `####` for **every section** (Action Items, each topic, Decisions, Participant Notes, Next Steps).
- Use `#####` or bullets for sub-content inside a section.

Never use `##` or `#` for a section — they place nodes outside the meeting-title scope and break the hierarchy.

---

## FULL PROMPT — paste everything below the line

---

### CONTEXT (replace with your own — 2–4 lines)

> My name is **[Your Name]**. I [your role] and run my work out of meetings with a small set of
> recurring collaborators — for example a direct report, a cross-functional peer, and my manager.
> I use these summaries to extract action items, decisions, and notes on the people I work with.

### GLOSSARY (replace with your own; delete if none)

| Term | Meaning |
|------|---------|
| **[ACRONYM]** | [what it stands for] |
| **[Project name]** | [one-line description so the model doesn't mistake it for something else] |
| **[Internal tool]** | [what it is — helps the model not "correct" it to a similar real word] |

### INSTRUCTIONS

Write a summary of the meeting transcript. Format as hierarchical Markdown with headings and bullet points.

**Do NOT include:** a main "Summary" heading, the meeting title as a separate element, an attendees
list, the date, or the time.

**Before writing:**
1. Read the transcript carefully.
2. Infer the meeting type (review, planning, 1:1, cross-functional, etc.) — reflect it in the
   structure; don't state it explicitly.
3. If an attendees list is provided, use it for context.
4. Never reference generic speaker labels ("Speaker 1") directly.

**Language:** English (translate to English even if the transcript is in another language).

**Formatting:**
- Minimal font-size difference between headings and body.
- Minimal spacing between sections.
- Dense and comprehensive — capture all ideas and action items.
- Heading levels: `###` for the meeting title only; `####` for every section below it; `#####` or
  bullets for sub-content. Never `##` or `#`.

### OUTPUT STRUCTURE

```
### [Meeting Title — reflecting what happened]

#### Action Items
- [One line per action item; include the owner's name if identifiable]
- ...

#### Completed / Closed in This Meeting
- [Any task or prior commitment explicitly confirmed done, resolved, cancelled, or dropped — note who
  confirmed it and brief context. e.g. "Tom confirmed the deck was shared", "Team decided not to pursue X"]
- [Omit this whole section if nothing was completed or closed]

#### [Topic 1]
- Key points discussed
- Decisions made

#### [Topic 2]
- Key points discussed
- Decisions made

... (continue for all topics)

#### Decisions
- [Each clear decision on one line — what was decided, plus the owner if relevant. A decision is a
  stated outcome + a commitment to act, not act, or change a rule. Exclude open questions, status
  updates, and ideas that were floated but not committed.]

#### Participant Notes
- [For each named person who actively participated, capture 1–3 observations worth keeping — only if
  specific, evidenced, and new (not just their role). Use a direct quote or moment as evidence. Omit
  this section for town halls / pure-broadcast meetings with no real discussion.]
- Look for these signals per person:
  - **Position** — a contested view they argued for or defended (what it was, any pushback, did they hold or update it)
  - **Behavioral Pattern** — a recurring mode this meeting (deflection, over-agreeing, probing before proposing, anchoring early) — only if it appeared 2+ times or was pronounced
  - **Desire** — what they were visibly pushing toward (a resource, an outcome, a path)
  - **Concern** — what they were resisting or worried about (pushback, expressed risk, hesitation)
  - **Strength** — a notable capability shown (data command, structured thinking, facilitation, composure)
- **Relationship dynamics** — if two participants showed visible tension, coalition, bypass, or
  strong alignment on a contested point, note it: "[Person A] ↔ [Person B]: [dynamic + evidence]"

#### Next Steps
- [Next review/follow-up date, any pre-reads needed, anything forward-looking that isn't already an action item]
```

---

## MINIMAL PROMPT — copy-paste ready

For summarizers that do better with a shorter prompt. Same structure, fewer words.

---

My name is **[Your Name]**. [One line on your role and who your recurring collaborators are.]

Write a meeting summary as hierarchical Markdown. Do NOT include a "Summary" heading, attendees,
date, or time. Infer the meeting type from the transcript and reflect it in the structure. Never
reference "Speaker 1" etc. directly. English only. Dense content, minimal spacing.

Heading levels: `###` for the meeting title only; `####` for every section. Never `##` or `#`.

```
### [Meeting Title — reflecting what happened]

#### Action Items
- [One line each; include the owner if identifiable]

#### [Topic sections]
- Key points, decisions

#### Decisions
- [Each committed decision on one line, owner if relevant]

#### Participant Notes
- [Per active participant: 1–3 evidenced observations — Position / Behavioral Pattern / Desire /
  Concern / Strength. Quote-backed only. Omit for broadcast-only meetings.]

#### Next Steps
- [Follow-up date, pre-reads, forward-looking items]
```

---

## (Optional) Soft-skill / self-coaching add-on

If you also want the summarizer to assess *your own* communication in the meeting (a personal
coaching habit, not part of the core action-items flow), append a `#### Self Assessment` section to
the structure asking it to quote a few of your statements and note where you were concise vs.
over-explained, whether you led with the conclusion, whether you assigned clear owners/timelines, and
one thing to practice next time. Keep it quote-driven so you can verify which lines were actually
yours (transcripts usually aren't speaker-labelled). This is entirely optional — strip it if you only
want clean minutes.
