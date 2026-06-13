# Demo Workspace — the worked-example used across every skill

Every example in this repo is written against **one fictional Tana workspace** so the
skills stay consistent and you can follow a single story end-to-end. Nothing here is
real — all node IDs, people, and data are invented. When you adapt a skill to your own
Tana, you swap these IDs for yours (see [GETTING-STARTED.md](../GETTING-STARTED.md) →
"Finding your own IDs").

> **ID convention:** every fake ID is prefixed `demo…` so it's obvious it's a placeholder.
> Real Tana node IDs are opaque 11–13 char strings like `Cq2lnUIBBr_Q`. Yours will look
> like that; ours look like `demoTaskTag1` on purpose.

---

## The story

You are **a solo operator / small-team lead** running your work out of Tana, with
Claude Code wired in as the intelligence layer. You run meetings, delegate tasks, track
decisions, and keep notes on the people you work with. Three recurring collaborators:

| Person | Demo ID | Role in the story |
|--------|---------|-------------------|
| **Riya Sharma** | `demoRiya0001` | Your direct report — most delegated tasks land on her |
| **Tom Becker** | `demoTom00002` | A cross-functional peer — joint owner on shared work |
| **Maya Chen** | `demoMaya0003` | Your manager — senior stakeholder in upward meetings |
| **You** | `demoYou00000` | The default assignee for your own action items |

Three domains (Context values) your work splits into:

| Context | Demo ID |
|---------|---------|
| **Product** | `demoCtxProd1` |
| **Sales** | `demoCtxSales` |
| **Hiring** | `demoCtxHire1` |

---

## Supertags & field IDs

These are the supertags the skills read and write. Field IDs are fictional; the **shape**
mirrors a real Tana setup.

### `#Task` — `demoTaskTag1`
| Field | Demo ID | Type | Notes |
|-------|---------|------|-------|
| Assignee | `demoFldAsgn1` | Instance of #Person | multi-value |
| Context | `demoFldCtx01` | Instance of #Context | multi-value |
| Urgency | `demoFldUrg01` | Options | see below |
| Due date | `demoFldDue01` | Date | team tasks should have one |
| Parent Meeting | `demoFldPMtg1` | Instance of #Meeting | the canonical link back to the meeting |

**Urgency options:** Critical `demoUrgCrit1` · Fast-Track `demoUrgFast1` · Normal `demoUrgNorm1` · Someday/Maybe `demoUrgSome1`

### `#Meeting` — `demoMeetTag1`
| Field | Demo ID | Type |
|-------|---------|------|
| Date | `demoFldMDate` | Date |
| Attendees | `demoFldAtnd1` | Instance of #Person (multi) |
| Agenda | `demoFldAgnd1` | Plain text |
| Transcript | `demoFldTrns1` | child node holding transcript lines |
| Summary | `demoFldSumm1` | child node (AI-generated) |
| My Role | `demoFldRole1` | Options: Lead `demoRoleLead` · Peer `demoRolePeer` · Subordinate `demoRoleSub1` · Listener `demoRoleLstn` |

### `#Person` — `demoPersTag1`
| Field | Demo ID | Type |
|-------|---------|------|
| Email | `demoFldMail1` | Instance of #E-Mail |
| Role | `demoFldPRole` | Options |
| Company | `demoFldComp1` | Instance of #Company |

### `#Decision` — `demoDecTag01`
| Field | Demo ID | Type |
|-------|---------|------|
| Outcome | `demoFldOutc1` | Plain text |
| Date | `demoFldDDate` | Date |
| Context | `demoFldDCtx1` | Instance of #Context |

### `#PersonObservation` — `demoObsTag01`
| Field | Demo ID | Type |
|-------|---------|------|
| Person | `demoFldOPrsn` | Instance of #Person |
| Type | `demoFldOType` | Options: Position `demoObsPos01` · Behavioral Pattern `demoObsBeh01` · Desire `demoObsDes01` · Concern `demoObsCon01` · Strength `demoObsStr01` |
| Date | `demoFldODate` | Date |
| Observation | `demoFldOText` | Plain text |
| Quote | `demoFldOQuot` | Plain text |

---

## Containers & entry points

| Thing | Demo ID |
|-------|---------|
| Workspace | `demoWorkspace` |
| Home node | `demoHomeNode` |
| Decision Log (where #Decision nodes live) | `demoDecLog001` |
| People container | `demoPeople001` |

---

## A worked scenario (used by the action-items + meeting-brain examples)

> **Meeting:** "Q3 Roadmap Sync" (`demoMtgQ3Road`), attendees You + Riya + Tom, Context = Product.
> **Transcript node:** `demoTrnsQ3001`.
> In it: you agree Riya will draft the pricing one-pager by Friday, Tom will pull the
> churn numbers, and you decide to cut the legacy import feature. Riya pushes back on the
> timeline (a behavioral signal worth capturing). That single meeting feeds every example:
> tasks (Riya/Tom), a decision (cut legacy import), a person observation (Riya — Concern
> about timeline), and live coaching flags from the meeting brain.
