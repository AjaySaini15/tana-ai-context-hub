---
name: tana-schema-graph
description: Visualize Tana supertag schemas as interactive force-directed graphs
argument-hint: "[tag name or part of system]"
---

# Skill: Tana Schema Graph

Create interactive, zero-dependency HTML visualizations of Tana supertag schemas. Shows tag hierarchies, fields, and relationships.

> Examples in this skill use the fictional workspace from
> [`demo-workspace/DEMO-WORKSPACE.md`](../../demo-workspace/DEMO-WORKSPACE.md). All node
> IDs shown (e.g. `demoTaskTag1`) are placeholders — swap them for your own. See
> [`GETTING-STARTED.md`](../../GETTING-STARTED.md) → "Finding your own IDs".

## Philosophy

1. **Use cheap exploration** — Spin up a cheap subagent (e.g., Haiku) to fetch tag schemas via MCP tools
2. **Scope carefully** — Large schemas don't visualize well; focus on branches or subsystems rather than entire workspaces
3. **Show fields as nodes** — Reveals which tags share fields and instance relationships
4. **Dynamic branches** — Colors auto-assigned based on root elements discovered
5. **Zero dependencies** — Single HTML file, runs forever

---

## Quick Start

If user provides argument: `/tana-schema-graph Tasks` or `/tana-schema-graph my meeting tags`
- Search for the tag or explore the described part of their system

If no argument, ask what part of their schema to visualize.

---

## Phase 1: Understand Scope

Ask what to visualize:

> "What part of your Tana schema should I visualize? You can share:
> - A tag name to start from (e.g., 'Task', 'Meeting')
> - A group of related tags (e.g., 'my task-related tags')
> - A subsystem (e.g., 'the people/CRM part of my system')"

**Important:** Steer users toward focused subsets. Entire workspace schemas become cluttered and hard to read. If the user asks for "all tags" or something very broad, suggest breaking it into branches.

Based on response, determine:
- **Starting point(s)**: One or more root tags to explore from
- **Depth**: How many levels of inheritance to include
- **Include fields**: Whether to show field nodes (default: yes)

---

## Phase 2: Explore Schema (Use Cheap Subagent)

**Important**: Use a cheap subagent (e.g., Haiku) for schema exploration — it's mechanical lookup work.

The agent should:

1. **Load Tana MCP tools** via `ToolSearch`
2. **List workspaces** to get workspace ID
3. **For each starting tag**, use `get_tag_schema` to discover:
   - Parent tags (extends relationship)
   - Own fields with IDs and types
   - Field datatypes (content, date, url, options, instance)
   - For instance fields: the source supertag reference
4. **Recursively explore** parent tags and child tags
5. **Return structured data** in the schema format (see `schema-format.md`)

### Finding Child Tags

To find tags that extend a parent:
```json
search_nodes({ "and": [{"hasType": "<parent-tag-id>"}, {"is": "template"}] })
```

### Field Types

Map Tana datatypes to visualization types:
| Tana Datatype | Schema Type |
|---------------|-------------|
| SYS_D6 (Plain text) | content |
| SYS_D9 (Date) | date |
| SYS_D10 (URL) | url |
| SYS_D12 (Options) | options |
| Options from supertag | instance |

---

## Phase 3: Generate Visualization

### Build Schema Object

Structure the discovered data:

```javascript
const schema = {
    tags: [
        { id: 'local-id', name: 'Tag Name', tanaId: 'demoTaskTag1' },
        // ...
    ],
    fields: [
        { id: 'f-fieldname', name: 'Field Name', type: 'content|date|url|options|instance', tanaId: 'demoFldDue01' },
        // ...
    ],
    extends: [
        { from: 'child-id', to: 'parent-id' },
        // ...
    ],
    hasField: [
        { tag: 'tag-id', field: 'field-id' },
        // ...
    ],
    instanceOf: [
        { field: 'field-id', tag: 'target-tag-id' },
        // Only for instance-type fields
    ]
};
```

### Generate HTML

1. Use template from `html-template.md`
2. Replace `{{SCHEMA}}` with the schema object
3. Save to `./[schema-name]-schema.html`
4. Run `open [filename].html`

Tell user:

```
Your schema graph is ready: [filename].html

I've opened it in your browser. Drag nodes to rearrange, hover to see connections.

What would you like to adjust?
- **Add tags**: Include more of your schema
- **Remove clutter**: Hide certain fields or tags
- **Layout**: Adjust initial positions
```

---

## Phase 4: Iterate

Listen to feedback and refine:

- **"Add X tag"** — Fetch its schema and add to the graph
- **"Too cluttered"** — Offer to hide fields or simplify
- **"Wrong relationship"** — Verify with MCP and correct
- **"Export"** — Use the PDF button in the visualization

---

## Reference Files

1. **`html-template.md`** — Full HTML template with placeholders
2. **`schema-format.md`** — Schema data structure specification

---

## Tips

- Start small — visualize one branch first, expand as needed
- Instance fields are key — they show cross-branch relationships
- Depth-based sizing — root tags are largest, children smaller
- Branch colors auto-assign — no need to configure
