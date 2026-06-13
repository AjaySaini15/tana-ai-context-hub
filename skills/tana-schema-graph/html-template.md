# HTML Template

Base template for schema graph visualizations. Single self-contained HTML file with force-directed layout, hover interactions, and PDF export.

The `{{SCHEMA}}` placeholder is the only thing you replace — build that object from your
own tags (see `schema-format.md` for the structure and a complete demo-workspace example).

## Full Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Schema Graph</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
:root{--bg:#f9f8f6;--bg2:#ffffff;--c1:#1a1816;--c2:#6b635a;--c3:#a8a29e;--field:#78716c;--hasField:#e7e5e4;--font:'Outfit',system-ui,sans-serif}
@media(prefers-color-scheme:dark){:root{--bg:#0f0e0d;--bg2:#1a1918;--c1:#f5f3f0;--c2:#a8a29e;--c3:#6b635a;--hasField:#2a2826}}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:var(--font);background:var(--bg);color:var(--c1);overflow:hidden;height:100dvh}
svg{display:block;width:100%;height:100%}

.node{cursor:grab;transition:opacity .2s ease-out}
.node:active{cursor:grabbing}
.node.tag circle{transition:transform .15s ease-out,filter .15s ease-out}
.node.field rect{fill:var(--field);transition:transform .15s ease-out,filter .15s ease-out}
.node:hover circle,.node:hover rect{transform:scale(1.12);filter:brightness(1.05)}
.node:active circle,.node:active rect{transform:scale(1.05);filter:brightness(0.95)}
.node .icon{fill:#fff;stroke:#fff;stroke-width:0}
.node .name{fill:var(--c1);font-size:12px;font-weight:500;text-anchor:middle;transition:opacity .2s ease-out}
.node.field .name{font-size:10px;fill:var(--c2)}

.node.dimmed{opacity:.7}
.link.dimmed{opacity:.4}

.link{fill:none;stroke-width:1.5;transition:opacity .2s ease-out}
.link.extends{stroke-opacity:.8}
.link.hasField{stroke:var(--hasField);stroke-opacity:.6;stroke-width:1}
.link.instance{stroke-opacity:.7;stroke-dasharray:4 2}
.link.highlighted{stroke-width:2.5;stroke-opacity:1}

.legend{position:fixed;bottom:1.5rem;left:1.5rem;background:var(--bg2);border-radius:12px;padding:.75rem 1rem;font-size:.6rem;color:var(--c3);box-shadow:0 1px 3px rgba(0,0,0,.04),0 4px 12px rgba(0,0,0,.06);line-height:1.6;max-width:180px;opacity:.85;transition:opacity .2s ease-out}
.legend:hover{opacity:1}
.legend h3{font-size:.5rem;text-transform:uppercase;letter-spacing:.1em;margin-bottom:.35rem;color:var(--c2);font-weight:600}
.legend-row{display:flex;gap:.35rem;margin-bottom:.25rem;flex-wrap:wrap}
.legend-chip{display:inline-flex;align-items:center;gap:.3rem;padding:.15rem .4rem;border-radius:4px;background:var(--bg);font-size:.55rem}
.legend-chip svg{width:10px;height:10px}
.legend-line{width:12px;height:0;border-top:2px solid var(--c3)}
.legend-line.dashed{border-top-style:dashed}

.title{position:fixed;top:2rem;left:2rem}
.title h1{font-size:1.35rem;font-weight:700;letter-spacing:-.02em}
.title p{font-size:.7rem;color:var(--c3);margin-top:.25rem;font-weight:400}

.legend-actions{display:flex;align-items:center;gap:.5rem;margin-top:.6rem;padding-top:.5rem;border-top:1px solid var(--hasField)}
.btn{font-family:var(--font);font-size:.55rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--c2);background:transparent;border:0;cursor:pointer;padding:.3rem .1rem;transition:color .15s;display:flex;align-items:center;gap:.3rem}
.btn:hover{color:var(--c1)}
.btn svg{width:12px;height:12px;stroke:currentColor;stroke-width:1.5;fill:none}
.legend-brand{margin-left:auto;font-size:.5rem;font-weight:500;letter-spacing:.04em;color:var(--c3);text-decoration:none;opacity:.5;transition:opacity .15s}
.legend-brand:hover{opacity:.8}
.brand-full{display:none}
.brand-short{display:inline}

@media print{
    html,body{margin:0;padding:0;overflow:hidden;height:100%;background:#fff!important}
    .tooltip,.title{display:none!important}
    .legend{position:fixed;bottom:1rem;left:1.5rem;z-index:10;background:#fff;opacity:1;box-shadow:none}
    .legend,.legend h3,.legend-chip{color:#6b635a}
    .legend svg{display:none}
    .legend-actions .btn{display:none}
    .legend-brand{opacity:1;color:#6b635a}
    .brand-short{display:none}
    .brand-full{display:inline}
    svg{position:fixed;top:0;left:0;width:100vw;height:100vh;background:#fff}
    .node .name{fill:#1a1816!important}
    .node.field .name{fill:#6b635a!important}
    .link.hasField{stroke:#d4d4d4!important}
    @page{size:landscape;margin:0}
}

.tooltip{position:fixed;background:var(--c1);color:var(--bg);padding:.35rem .55rem;border-radius:5px;font-size:.7rem;font-weight:500;pointer-events:none;opacity:0;transition:opacity .15s ease-out;z-index:100;white-space:nowrap}
.tooltip.visible{opacity:1}
    </style>
</head>
<body>
<div class="title">
    <h1>Schema Graph</h1>
    <p>Hover to explore connections</p>
</div>
<div class="tooltip" id="tooltip"></div>

<svg id="graph">
    <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--extends)"/>
        </marker>
        <filter id="text-bg" x="-50%" y="-50%" width="200%" height="200%">
            <feFlood flood-color="var(--bg)" flood-opacity="0.9" result="bg"/>
            <feMorphology in="SourceAlpha" radius="3" operator="dilate" result="dilated"/>
            <feComposite in="bg" in2="dilated" operator="in" result="bg-text"/>
            <feMerge>
                <feMergeNode in="bg-text"/>
                <feMergeNode in="SourceGraphic"/>
            </feMerge>
        </filter>
        <symbol id="icon-text" viewBox="0 0 16 16">
            <path d="M3 4h10M3 8h8M3 12h6" stroke="#fff" stroke-width="2" stroke-linecap="round" fill="none"/>
        </symbol>
        <symbol id="icon-date" viewBox="0 0 16 16">
            <rect x="2" y="3" width="12" height="11" rx="1" stroke="#fff" stroke-width="1.5" fill="none"/>
            <path d="M2 6h12M5 1v3M11 1v3" stroke="#fff" stroke-width="1.5" stroke-linecap="round" fill="none"/>
        </symbol>
        <symbol id="icon-url" viewBox="0 0 16 16">
            <path d="M6.5 9.5a3 3 0 004.2.2l1.8-1.8a3 3 0 00-4.2-4.2L7 5M9.5 6.5a3 3 0 00-4.2-.2L3.5 8.1a3 3 0 004.2 4.2L9 11" stroke="#fff" stroke-width="1.5" stroke-linecap="round" fill="none"/>
        </symbol>
        <symbol id="icon-options" viewBox="0 0 16 16">
            <circle cx="4" cy="4" r="1.5" fill="#fff"/>
            <circle cx="4" cy="8" r="1.5" fill="#fff"/>
            <circle cx="4" cy="12" r="1.5" fill="#fff"/>
            <path d="M7 4h6M7 8h6M7 12h6" stroke="#fff" stroke-width="1.5" stroke-linecap="round"/>
        </symbol>
        <symbol id="icon-tag" viewBox="0 0 16 16">
            <text x="8" y="13" text-anchor="middle" fill="#fff" font-size="14" font-weight="700">#</text>
        </symbol>
    </defs>
</svg>

<div class="legend">
    <h3>Branches</h3>
    <div class="legend-row" id="legend-branches"></div>
    <h3 style="margin-top:.4rem">Connections</h3>
    <div class="legend-row">
        <div class="legend-chip"><div class="legend-line"></div>extends</div>
        <div class="legend-chip"><div class="legend-line" style="border-color:var(--hasField)"></div>has field</div>
        <div class="legend-chip"><div class="legend-line dashed"></div>instance</div>
    </div>
    <div class="legend-actions">
        <button class="btn" id="btn-print" title="Save as PDF">
            <svg viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            PDF
        </button>
        <a class="legend-brand" href="https://tana.inc" target="_blank"><span class="brand-short">tana.inc</span><span class="brand-full">Created with tana.inc</span></a>
    </div>
</div>

<script>
const iconMap = { content: 'icon-text', date: 'icon-date', url: 'icon-url', options: 'icon-options', instance: 'icon-tag' };

// {{SCHEMA}} - Replace this with the generated schema object
const schema = {{SCHEMA}};

const svg = document.getElementById('graph');
let width = window.innerWidth;
let height = window.innerHeight;

// Build nodes
const nodeMap = new Map();
schema.tags.forEach(t => nodeMap.set(t.id, { ...t, nodeType: 'tag', x: width/2, y: height/2, vx: 0, vy: 0 }));
schema.fields.forEach(f => nodeMap.set(f.id, { ...f, nodeType: 'field', x: width/2, y: height/2, vx: 0, vy: 0 }));
const nodes = Array.from(nodeMap.values());

// Calculate depth and branch for tags
const parentMap = new Map();
schema.extends.forEach(e => parentMap.set(e.from, e.to));

function getDepth(id, visited = new Set()) {
    if (visited.has(id)) return 0;
    visited.add(id);
    const parent = parentMap.get(id);
    return parent ? 1 + getDepth(parent, visited) : 0;
}

function getRoot(id, visited = new Set()) {
    if (visited.has(id)) return id;
    visited.add(id);
    const parent = parentMap.get(id);
    return parent ? getRoot(parent, visited) : id;
}

// Discover root elements and generate colors
const roots = schema.tags.filter(t => !parentMap.has(t.id)).map(t => t.id);
const palette = ['#6366f1','#10b981','#a855f7','#f97316','#ec4899','#14b8a6','#f59e0b','#8b5cf6'];
const branchColors = {};
roots.forEach((root, i) => {
    branchColors[root] = palette[i % palette.length];
});

// Populate legend dynamically
const legendBranches = document.getElementById('legend-branches');
roots.forEach(rootId => {
    const tag = schema.tags.find(t => t.id === rootId);
    const chip = document.createElement('div');
    chip.className = 'legend-chip';
    chip.innerHTML = `<svg viewBox="0 0 14 14"><circle cx="7" cy="7" r="6" fill="${branchColors[rootId]}"/></svg>${tag?.name || rootId}`;
    legendBranches.appendChild(chip);
});

nodes.filter(n => n.nodeType === 'tag').forEach(n => {
    n.depth = getDepth(n.id);
    n.root = getRoot(n.id);
    n.branchColor = branchColors[n.root] || palette[0];
    n.radius = Math.max(16, 30 - n.depth * 4);
});

// Build links
const links = [
    ...schema.extends.map(e => ({ source: nodeMap.get(e.from), target: nodeMap.get(e.to), type: 'extends' })),
    ...schema.hasField.map(e => ({ source: nodeMap.get(e.tag), target: nodeMap.get(e.field), type: 'hasField' })),
    ...(schema.instanceOf || []).map(e => ({ source: nodeMap.get(e.field), target: nodeMap.get(e.tag), type: 'instance' }))
];

// Initial positions - spread by depth
const depthGroups = {};
nodes.filter(n => n.nodeType === 'tag').forEach(n => {
    if (!depthGroups[n.depth]) depthGroups[n.depth] = [];
    depthGroups[n.depth].push(n);
});

Object.entries(depthGroups).forEach(([depth, tags]) => {
    const y = 0.12 + parseInt(depth) * 0.18;
    tags.forEach((n, i) => {
        n.x = width * (0.1 + (i / Math.max(1, tags.length - 1)) * 0.8);
        n.y = height * Math.min(y, 0.7);
    });
});

// Position fields near their first owning tag
const fieldOwners = new Map();
schema.hasField.forEach(hf => {
    if (!fieldOwners.has(hf.field)) fieldOwners.set(hf.field, hf.tag);
});
nodes.filter(n => n.nodeType === 'field').forEach(n => {
    const ownerTag = nodeMap.get(fieldOwners.get(n.id));
    if (ownerTag) {
        const angle = Math.random() * Math.PI * 0.5 + Math.PI * 0.25;
        const dist = 60 + Math.random() * 40;
        n.x = ownerTag.x + Math.cos(angle) * dist;
        n.y = ownerTag.y + Math.sin(angle) * dist;
    } else {
        n.x = width * 0.5;
        n.y = height * 0.8;
    }
});

// SVG groups
const linkGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
const nodeGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
svg.appendChild(linkGroup);
svg.appendChild(nodeGroup);

// Create links
links.forEach(link => {
    if (!link.source || !link.target) return;
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.classList.add('link', link.type);

    if (link.type === 'extends') {
        const color = link.source.branchColor || palette[0];
        path.style.stroke = color;
        const markerId = 'arrow-' + link.source.root;
        if (!document.getElementById(markerId)) {
            const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
            marker.setAttribute('id', markerId);
            marker.setAttribute('viewBox', '0 0 10 10');
            marker.setAttribute('refX', '8');
            marker.setAttribute('refY', '5');
            marker.setAttribute('markerWidth', '5');
            marker.setAttribute('markerHeight', '5');
            marker.setAttribute('orient', 'auto-start-reverse');
            const arrowPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            arrowPath.setAttribute('d', 'M 0 0 L 10 5 L 0 10 z');
            arrowPath.style.fill = color;
            marker.appendChild(arrowPath);
            document.querySelector('defs').appendChild(marker);
        }
        path.setAttribute('marker-end', `url(#${markerId})`);
    } else if (link.type === 'instance') {
        const color = link.target.branchColor || palette[0];
        path.style.stroke = color;
    }

    link.el = path;
    linkGroup.appendChild(path);
});

// Create nodes
nodes.forEach(node => {
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.classList.add('node', node.nodeType);

    if (node.nodeType === 'tag') {
        const r = node.radius || 22;
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('r', r);
        circle.style.fill = node.branchColor;
        g.appendChild(circle);

        const iconSize = Math.round(r * 0.8);
        const icon = document.createElementNS('http://www.w3.org/2000/svg', 'use');
        icon.setAttribute('href', '#icon-tag');
        icon.setAttribute('x', -iconSize/2);
        icon.setAttribute('y', -iconSize/2);
        icon.setAttribute('width', iconSize);
        icon.setAttribute('height', iconSize);
        g.appendChild(icon);
    } else {
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('width', 28);
        rect.setAttribute('height', 28);
        rect.setAttribute('x', -14);
        rect.setAttribute('y', -14);
        rect.setAttribute('rx', 5);
        g.appendChild(rect);

        const iconId = iconMap[node.type] || 'icon-text';
        const icon = document.createElementNS('http://www.w3.org/2000/svg', 'use');
        icon.setAttribute('href', '#' + iconId);
        icon.setAttribute('x', -9);
        icon.setAttribute('y', -9);
        icon.setAttribute('width', 18);
        icon.setAttribute('height', 18);
        g.appendChild(icon);
    }

    const nameText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    nameText.classList.add('name');
    nameText.setAttribute('filter', 'url(#text-bg)');
    const textOffset = node.nodeType === 'tag' ? (node.radius || 22) + 14 : 32;
    nameText.setAttribute('dy', textOffset);
    nameText.textContent = node.name;
    g.appendChild(nameText);

    // Drag
    let dragging = false;
    g.addEventListener('mousedown', e => { dragging = true; node.fx = node.x; node.fy = node.y; e.preventDefault(); });
    document.addEventListener('mousemove', e => {
        if (!dragging) return;
        node.fx = e.clientX; node.fy = e.clientY;
        node.x = e.clientX; node.y = e.clientY;
    });
    document.addEventListener('mouseup', () => { if (dragging) { dragging = false; node.fx = null; node.fy = null; } });

    // Hover highlight
    g.addEventListener('mouseenter', e => {
        if (dragging) return;
        highlightConnections(node);
        showTooltip(node, e);
    });
    g.addEventListener('mouseleave', () => {
        clearHighlight();
        hideTooltip();
    });
    g.addEventListener('mousemove', e => {
        if (!dragging) updateTooltipPosition(e);
    });

    node.el = g;
    nodeGroup.appendChild(g);
});

// Tooltip
const tooltip = document.getElementById('tooltip');
function showTooltip(node, e) {
    tooltip.textContent = node.name;
    tooltip.classList.add('visible');
    updateTooltipPosition(e);
}
function updateTooltipPosition(e) {
    tooltip.style.left = (e.clientX + 12) + 'px';
    tooltip.style.top = (e.clientY - 8) + 'px';
}
function hideTooltip() {
    tooltip.classList.remove('visible');
}

// Highlight connections
function highlightConnections(node) {
    const connected = new Set([node.id]);
    const connectedLinks = new Set();

    links.forEach(link => {
        if (link.source?.id === node.id || link.target?.id === node.id) {
            connected.add(link.source?.id);
            connected.add(link.target?.id);
            connectedLinks.add(link);
        }
    });

    nodes.forEach(n => {
        n.el.classList.toggle('dimmed', !connected.has(n.id));
    });

    links.forEach(link => {
        if (connectedLinks.has(link)) {
            link.el.classList.remove('dimmed');
            link.el.classList.add('highlighted');
        } else {
            link.el.classList.add('dimmed');
            link.el.classList.remove('highlighted');
        }
    });
}

function clearHighlight() {
    nodes.forEach(n => n.el.classList.remove('dimmed'));
    links.forEach(l => {
        l.el.classList.remove('dimmed');
        l.el.classList.remove('highlighted');
    });
}

// Simulation
function simulate() {
    for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
            const a = nodes[i], b = nodes[j];
            let dx = b.x - a.x, dy = b.y - a.y;
            let dist = Math.sqrt(dx * dx + dy * dy) || 1;
            let strength = (a.nodeType === b.nodeType) ? 1200 : 600;
            let force = strength / (dist * dist);
            if (!a.fx) { a.vx -= (dx/dist)*force; a.vy -= (dy/dist)*force; }
            if (!b.fx) { b.vx += (dx/dist)*force; b.vy += (dy/dist)*force; }
        }
    }

    links.forEach(link => {
        if (!link.source || !link.target) return;
        let dx = link.target.x - link.source.x, dy = link.target.y - link.source.y;
        let dist = Math.sqrt(dx * dx + dy * dy) || 1;
        let ideal = link.type === 'extends' ? 120 : link.type === 'instance' ? 130 : 80;
        let str = link.type === 'hasField' ? 0.03 : 0.015;
        let force = (dist - ideal) * str;
        if (!link.source.fx) { link.source.vx += (dx/dist)*force; link.source.vy += (dy/dist)*force; }
        if (!link.target.fx) { link.target.vx -= (dx/dist)*force; link.target.vy -= (dy/dist)*force; }
    });

    nodes.forEach(n => {
        if (n.fx) return;
        n.vx += (width/2 - n.x) * 0.00005;
        n.vy += (height/2 - n.y) * 0.00005;
        n.vx *= 0.9; n.vy *= 0.9;
        n.x += n.vx; n.y += n.vy;
        n.x = Math.max(60, Math.min(width - 60, n.x));
        n.y = Math.max(60, Math.min(height - 80, n.y));
    });

    nodes.forEach(n => n.el.setAttribute('transform', `translate(${n.x},${n.y})`));

    links.forEach(link => {
        if (!link.source || !link.target || !link.el) return;
        const sx = link.source.x, sy = link.source.y, tx = link.target.x, ty = link.target.y;
        const dx = tx - sx, dy = ty - sy, dist = Math.sqrt(dx*dx + dy*dy) || 1;
        const nx = dx/dist, ny = dy/dist;
        const ss = link.source.nodeType === 'tag' ? (link.source.radius || 22) : 14;
        const ts = link.target.nodeType === 'tag' ? (link.target.radius || 22) : 14;
        const ao = link.type === 'extends' ? 5 : 0;
        const x1 = sx + nx*ss, y1 = sy + ny*ss;
        const x2 = tx - nx*(ts+ao), y2 = ty - ny*(ts+ao);
        const curve = link.type === 'instance' ? 0.2 : link.type === 'extends' ? 0.03 : 0;
        const mx = (x1+x2)/2, my = (y1+y2)/2;
        const cx = mx - (y2-y1)*curve, cy = my + (x2-x1)*curve;
        link.el.setAttribute('d', curve ? `M${x1},${y1} Q${cx},${cy} ${x2},${y2}` : `M${x1},${y1} L${x2},${y2}`);
    });

    requestAnimationFrame(simulate);
}

// Pre-settle
function tick() {
    for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
            const a = nodes[i], b = nodes[j];
            let dx = b.x - a.x, dy = b.y - a.y;
            let dist = Math.sqrt(dx * dx + dy * dy) || 1;
            let strength = (a.nodeType === b.nodeType) ? 1200 : 600;
            let force = strength / (dist * dist);
            if (!a.fx) { a.vx -= (dx/dist)*force; a.vy -= (dy/dist)*force; }
            if (!b.fx) { b.vx += (dx/dist)*force; b.vy += (dy/dist)*force; }
        }
    }
    links.forEach(link => {
        if (!link.source || !link.target) return;
        let dx = link.target.x - link.source.x, dy = link.target.y - link.source.y;
        let dist = Math.sqrt(dx * dx + dy * dy) || 1;
        let ideal = link.type === 'extends' ? 120 : link.type === 'instance' ? 130 : 80;
        let str = link.type === 'hasField' ? 0.03 : 0.015;
        let force = (dist - ideal) * str;
        if (!link.source.fx) { link.source.vx += (dx/dist)*force; link.source.vy += (dy/dist)*force; }
        if (!link.target.fx) { link.target.vx -= (dx/dist)*force; link.target.vy -= (dy/dist)*force; }
    });
    nodes.forEach(n => {
        if (n.fx) return;
        n.vx += (width/2 - n.x) * 0.00005;
        n.vy += (height/2 - n.y) * 0.00005;
        n.vx *= 0.9; n.vy *= 0.9;
        n.x += n.vx; n.y += n.vy;
        n.x = Math.max(60, Math.min(width - 60, n.x));
        n.y = Math.max(60, Math.min(height - 80, n.y));
    });
}

// Pin tags, settle fields, unpin
nodes.filter(n => n.nodeType === 'tag').forEach(n => { n.fx = n.x; n.fy = n.y; });
for (let i = 0; i < 300; i++) tick();
nodes.filter(n => n.nodeType === 'tag').forEach(n => { n.fx = null; n.fy = null; });

// Initial render
nodes.forEach(n => n.el.setAttribute('transform', `translate(${n.x},${n.y})`));
links.forEach(link => {
    if (!link.source || !link.target || !link.el) return;
    const sx = link.source.x, sy = link.source.y, tx = link.target.x, ty = link.target.y;
    const dx = tx - sx, dy = ty - sy, dist = Math.sqrt(dx*dx + dy*dy) || 1;
    const nx = dx/dist, ny = dy/dist;
    const ss = link.source.nodeType === 'tag' ? (link.source.radius || 22) : 14;
    const ts = link.target.nodeType === 'tag' ? (link.target.radius || 22) : 14;
    const ao = link.type === 'extends' ? 5 : 0;
    const x1 = sx + nx*ss, y1 = sy + ny*ss;
    const x2 = tx - nx*(ts+ao), y2 = ty - ny*(ts+ao);
    const curve = link.type === 'instance' ? 0.2 : link.type === 'extends' ? 0.03 : 0;
    const mx = (x1+x2)/2, my = (y1+y2)/2;
    const cx = mx - (y2-y1)*curve, cy = my + (x2-x1)*curve;
    link.el.setAttribute('d', curve ? `M${x1},${y1} Q${cx},${cy} ${x2},${y2}` : `M${x1},${y1} L${x2},${y2}`);
});

simulate();

// Resize
window.addEventListener('resize', () => {
    const oldW = width, oldH = height;
    width = window.innerWidth;
    height = window.innerHeight;
    const dx = (width - oldW) / 2;
    const dy = (height - oldH) / 2;
    nodes.forEach(n => { n.x += dx; n.y += dy; });
});

// Print / PDF
document.getElementById('btn-print').addEventListener('click', () => {
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    nodes.forEach(n => {
        const r = n.nodeType === 'tag' ? (n.radius || 22) : 14;
        minX = Math.min(minX, n.x - r - 50);
        minY = Math.min(minY, n.y - r - 20);
        maxX = Math.max(maxX, n.x + r + 50);
        maxY = Math.max(maxY, n.y + r + 50);
    });

    const padding = 60;
    let vbX = minX - padding;
    let vbY = minY - padding;
    let vbW = (maxX - minX) + padding * 2;
    let vbH = (maxY - minY) + padding * 2;

    const pageAspect = 1.35;
    const contentAspect = vbW / vbH;

    if (contentAspect < pageAspect) {
        const newW = vbH * pageAspect;
        vbX -= (newW - vbW) / 2;
        vbW = newW;
    } else {
        const newH = vbW / pageAspect;
        vbY -= (newH - vbH) / 2;
        vbH = newH;
    }

    const svgEl = document.getElementById('graph');
    const originalViewBox = svgEl.getAttribute('viewBox');
    svgEl.setAttribute('viewBox', `${vbX} ${vbY} ${vbW} ${vbH}`);

    window.print();

    setTimeout(() => {
        if (originalViewBox) {
            svgEl.setAttribute('viewBox', originalViewBox);
        } else {
            svgEl.removeAttribute('viewBox');
        }
    }, 100);
});
</script>
</body>
</html>
```

## Template Variable

| Variable | Description |
|----------|-------------|
| `{{SCHEMA}}` | JSON schema object (see `schema-format.md`) |

## Features

| Feature | Description |
|---------|-------------|
| **Force-directed layout** | Nodes repel, links attract, auto-settles |
| **Depth-based sizing** | Root tags largest, children progressively smaller |
| **Dynamic branches** | Colors auto-assigned from palette based on roots |
| **Hover highlight** | Dims unrelated nodes, shows direct connections |
| **Drag to rearrange** | Click and drag any node |
| **PDF export** | Fits to single landscape page |
| **Dark mode** | Auto-adapts to system preference |
