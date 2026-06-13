# Schema Format

The schema object defines all tags, fields, and relationships to visualize.

> The `tanaId` values below come from the fictional workspace in
> [`demo-workspace/DEMO-WORKSPACE.md`](../../demo-workspace/DEMO-WORKSPACE.md) (e.g.
> `demoTaskTag1`). Real Tana node IDs are opaque 11–13 char strings — replace these with
> your own. See [`GETTING-STARTED.md`](../../GETTING-STARTED.md) → "Finding your own IDs".

## Structure

```javascript
const schema = {
    tags: [...],      // Supertag definitions
    fields: [...],    // Field definitions
    extends: [...],   // Tag inheritance relationships
    hasField: [...],  // Which tags have which fields
    instanceOf: [...] // Instance field → target tag relationships
};
```

## Tags Array

Each tag is a supertag to display as a node.

```javascript
{
    id: 'local-id',          // Unique ID for internal references (kebab-case)
    name: 'Display Name',    // Name shown in visualization
    tanaId: 'demoTaskTag1'   // Actual Tana node ID
}
```

**Example:**
```javascript
tags: [
    { id: 'meeting', name: '▲ Meeting', tanaId: 'demoMeetTag1' },
    { id: 'task', name: 'task', tanaId: 'demoTaskTag1' },
    { id: 'person', name: 'person', tanaId: 'demoPersTag1' }
]
```

## Fields Array

Each field is displayed as a square node with a type icon.

```javascript
{
    id: 'f-fieldname',       // Unique ID, prefix with 'f-' by convention
    name: 'Field Name',      // Name shown in visualization
    type: 'content',         // One of: content, date, url, options, instance
    tanaId: 'demoFldDue01'   // Actual Tana field ID
}
```

**Field Types:**

| Type | Icon | Description |
|------|------|-------------|
| `content` | Text lines | Plain text or rich content |
| `date` | Calendar | Date picker field |
| `url` | Link | URL field |
| `options` | List dots | Static options dropdown |
| `instance` | # symbol | References instances of another supertag |

**Example:**
```javascript
fields: [
    { id: 'f-due-date', name: 'Due date', type: 'date', tanaId: 'demoFldDue01' },
    { id: 'f-assignee', name: 'Assignee', type: 'instance', tanaId: 'demoFldAsgn1' },
    { id: 'f-urgency', name: 'Urgency', type: 'options', tanaId: 'demoFldUrg01' }
]
```

## Extends Array

Defines tag inheritance (child → parent).

```javascript
{
    from: 'child-tag-id',   // Local ID of child tag
    to: 'parent-tag-id'     // Local ID of parent tag
}
```

**Example:**
```javascript
extends: [
    { from: 'task', to: 'work-item' },      // task extends work-item
    { from: 'milestone', to: 'work-item' }  // milestone extends work-item
]
```

Tags with no parent become "root" tags and get assigned branch colors.

## HasField Array

Defines which tags have which fields.

```javascript
{
    tag: 'tag-id',     // Local ID of tag
    field: 'field-id'  // Local ID of field
}
```

**Example:**
```javascript
hasField: [
    { tag: 'meeting', field: 'f-due-date' },
    { tag: 'task', field: 'f-due-date' },      // Shared field
    { tag: 'task', field: 'f-assignee' },
    { tag: 'task', field: 'f-urgency' }
]
```

Shared fields (used by multiple tags) will have multiple `hasField` entries and appear connected to all their owning tags.

## InstanceOf Array (Optional)

For `instance` type fields, defines which supertag they reference.

```javascript
{
    field: 'field-id',     // Local ID of instance field
    tag: 'target-tag-id'   // Local ID of target supertag
}
```

**Example:**
```javascript
instanceOf: [
    { field: 'f-assignee', tag: 'person' }  // Assignee references #person instances
]
```

This creates a dashed line from the field to the target tag, showing cross-branch relationships.

## Complete Example

This example uses the demo workspace's `#Task`, `#Person`, and `#Meeting` supertags. `#Task`
links to both `#Person` (via Assignee) and `#Meeting` (via Parent Meeting); `#Meeting` links
back to `#Person` (via Attendees) — so the instance dashed lines reveal how the three tags
interconnect.

```javascript
const schema = {
    tags: [
        { id: 'person',  name: '▲ Person',  tanaId: 'demoPersTag1' },
        { id: 'meeting', name: '▲ Meeting', tanaId: 'demoMeetTag1' },
        { id: 'task',    name: '▲ Task',    tanaId: 'demoTaskTag1' }
    ],

    fields: [
        { id: 'f-email',    name: 'Email',          type: 'url',      tanaId: 'demoFldMail1' },
        { id: 'f-mdate',    name: 'Date',           type: 'date',     tanaId: 'demoFldMDate' },
        { id: 'f-attendees',name: 'Attendees',      type: 'instance', tanaId: 'demoFldAtnd1' },
        { id: 'f-assignee', name: 'Assignee',       type: 'instance', tanaId: 'demoFldAsgn1' },
        { id: 'f-due',      name: 'Due date',       type: 'date',     tanaId: 'demoFldDue01' },
        { id: 'f-urgency',  name: 'Urgency',        type: 'options',  tanaId: 'demoFldUrg01' },
        { id: 'f-pmtg',     name: 'Parent Meeting', type: 'instance', tanaId: 'demoFldPMtg1' }
    ],

    extends: [],

    hasField: [
        { tag: 'person',  field: 'f-email' },
        { tag: 'meeting', field: 'f-mdate' },
        { tag: 'meeting', field: 'f-attendees' },
        { tag: 'task',    field: 'f-assignee' },
        { tag: 'task',    field: 'f-due' },
        { tag: 'task',    field: 'f-urgency' },
        { tag: 'task',    field: 'f-pmtg' }
    ],

    instanceOf: [
        { field: 'f-assignee',  tag: 'person' },
        { field: 'f-attendees', tag: 'person' },
        { field: 'f-pmtg',      tag: 'meeting' }
    ]
};
```

## Discovering Schema from Tana

Use MCP tools to build the schema:

1. **`get_tag_schema(tagId)`** returns:
   - `extends` array with parent tag IDs
   - `ownFields` array with field definitions

2. **For each field**, check:
   - `datatype` → maps to field type
   - `sourceSupertag` → if present, field is `instance` type

3. **To find child tags**:
   ```javascript
   search_nodes({ "and": [{"hasType": "<tag-id>"}, {"is": "template"}] })
   ```

## Visual Behavior

- **Root tags** (no parent): Largest size, assigned unique branch colors
- **Child tags**: Progressively smaller based on depth
- **Fields**: Gray squares, positioned near their first owning tag
- **Shared fields**: Connected to multiple tags, reveal cross-cutting concerns
- **Instance fields**: Dashed line to target tag, colored by target's branch
