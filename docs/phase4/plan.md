# Plan: Phase 4 — 2D Brain-Map Visualization (Obsidian-style)

> Builds on Phase 3. Upgrades the existing Cytoscape graph into a polished Obsidian-style 2D force graph.
> Library: Cytoscape.js — already in use, stay on CDN, no build step.
> Dark canvas, always-visible cluster labels, node size = comment volume, smooth pan/zoom.

---

## Dependency map

```
Slice 1 ──────────────────────────────────► (real data feeds Slice 2)
Slice 2 (mock data ok) ──► Slice 3 ──► Slice 4
```

**Batch 1 (fully parallel):** Slice 1 + Slice 2
- Slice 1 owns the backend endpoint; Slice 2 starts with the hardcoded `CLUSTER_DATA` Jinja blob
- Slice 2 swaps to the real endpoint once Slice 1 merges (a one-line change)

**Batch 2:** Slice 3 — needs Slice 2 merged (must know the Cytoscape instance and its event API)

**Batch 3:** Slice 4 — needs Slices 2 + 3 merged (polishes the fully wired graph)

---

## Slice 1 — Backend: GET clusters endpoint

**What to build**

A clean REST endpoint that returns clusters with their comments embedded, so the graph widget can fetch data independently of the Jinja template render cycle.

Files to create/touch:
- `app/models/comment_cluster.py` — add `to_dict(include_comments=False)`: when `True`, embed a `"comments"` list using each comment's `to_dict()`
- `app/routes/api.py` — add `GET /api/hearings/<id>/clusters`
  - Returns `200` with `[cluster.to_dict(include_comments=True), ...]`
  - Returns `404` if hearing not found
  - Returns `200` with `[]` if no clusters exist yet (not an error)

Implementation notes:
- Eager-load comments in the query (`joinedload`) — avoid N+1 on the comments relationship
- This endpoint also makes Phase 5 easier; design the response shape with that in mind

Acceptance:
- [ ] `GET /api/hearings/<id>/clusters` returns a JSON array of clusters, each with a `"comments"` array
- [ ] Returns `[]` (not 404) when no clusters have been run yet
- [ ] Returns 404 when the hearing doesn't exist
- [ ] Response includes `comment_count`, `name`, `description`, and `id` per cluster

---

## Slice 2 — Obsidian-style graph rendering

**Depends on:** Slice 1 data shape (start with existing `CLUSTER_DATA` Jinja blob — one-line swap when Slice 1 lands)

**What to build**

Restyle the existing Cytoscape graph to match the Obsidian graph aesthetic: dark canvas, glowing cluster nodes, muted comment dots, always-visible cluster name labels, smooth force layout.

Files to touch:
- `app/templates/hearings/detail.html`
  - Keep `<div id="cy">` and Cytoscape CDN tag — no library swap
  - Rewrite the Cytoscape style block and layout config (see below)
- `app/static/style.css` — dark background for `#cy`, expand container height (500–600px)

**Visual spec (Obsidian-like):**

Canvas: near-black background (`#0d1117` or similar).

Cluster nodes:
- Circle, radius proportional to `comment_count` — use `width: mapData(comment_count, 1, 20, 40, 120)` (Cytoscape mapper)
- Fill: the existing color palette, at ~80% opacity
- Soft glow: `shadow-blur: 18`, `shadow-color` matching the node color
- Label: cluster name, always visible, white, centered inside the node, `font-weight: bold`, `text-wrap: wrap`, `text-max-width` tied to node width

Comment nodes:
- Fixed small circle (16px), muted grey (`#4a4a5a`), no label
- No glow

Edges:
- Width: 1px, color `#2a2a3a` (very dark, subtle)
- `curve-style: haystack` (straight lines, performant)

Layout: `cose` — same as current, but tune for Obsidian spacing:
```js
{
  name: 'cose',
  animate: true,
  animationDuration: 600,
  nodeRepulsion: 12000,
  idealEdgeLength: 100,
  gravity: 0.25,
  fit: true,
  padding: 40
}
```

Implementation notes:
- `mapData()` is a built-in Cytoscape style mapper — no custom JS needed for sizing
- The existing `CLUSTER_DATA` structure (cluster nodes + comment nodes + edges) is already correct; only the style block changes
- Keep `animate: false` on initial load if performance is a concern with many nodes; set to `true` for re-clustering runs so the transition is visible

Acceptance:
- [ ] Graph renders on a dark canvas with Obsidian-style visuals
- [ ] Cluster node size visually reflects `comment_count`
- [ ] Cluster names are always visible inside their nodes (no hover required)
- [ ] Comment nodes are small and visually subordinate to cluster nodes
- [ ] Force layout runs and settles cleanly with the new parameters
- [ ] Empty state still renders correctly when no clusters exist

---

## Slice 3 — Drill-down panel + click wiring

**Depends on:** Slice 2 merged (needs the Cytoscape instance `cy` and its event API)

**What to build**

A slide-in right-side panel that populates when a cluster node is clicked. Pure DOM — no Cytoscape. The graph remains interactive behind the panel.

Files to touch:
- `app/templates/hearings/detail.html`
  - Add panel HTML (sibling of `#cy`, positioned absolutely over the right 35% of the container)
  - Wire `cy.on('tap', 'node[type="cluster"]', ...)` to populate and show the panel
  - Wire `cy.on('tap', 'node[type="comment"]', ...)` to do nothing (prevent accidental opens)
  - Wire `cy.on('tap', function(e) { if (e.target === cy) closePanel(); })` — tap canvas background closes
  - Add close button handler + `Escape` key listener
- `app/static/style.css` — panel styles: slide-in transition, scrollable comment list

Panel content (populated from clicked node data):
```
[×]  Affordability                    ← cluster name, close button
     "Comments expressing concern…"   ← cluster description
     ─────────────────────────────
     ● Rent is already too high here
     ● We can't afford another fee
     ● …
```

Implementation notes:
- Store the cluster's `comments` array directly on the Cytoscape node's `data` object at build time (pull from `CLUSTER_DATA`)
- Panel open/close is a CSS class toggle (`panel--open`) with `transform: translateX` transition
- Do not re-fetch on click — all comment text is already in the node's data
- When the panel opens, also run `cy.animate({ fit: { eles: clickedNode, padding: 80 } }, { duration: 400 })` to center the selected node — this is the 2D equivalent of a camera fly-to

Acceptance:
- [ ] Clicking a cluster node opens the panel with its name, description, and full comment list
- [ ] Clicking a comment node does nothing (no panel, no error)
- [ ] Clicking the canvas background closes the panel
- [ ] Pressing Escape closes the panel
- [ ] Comment list scrolls independently when it overflows
- [ ] The graph pans/zooms to center the selected cluster node when the panel opens
- [ ] Panel is not visible on initial load

---

## Slice 4 — Hover highlights + visual polish

**Depends on:** Slices 2 + 3 merged

**What to build**

Hover feedback, node selection state, and responsive sizing. Makes the graph feel like a real Obsidian graph.

Files to touch:
- `app/templates/hearings/detail.html` — hover and selection event handlers
- `app/static/style.css` — selected/dimmed state styles, responsive container

**Hover on cluster node:**
- Highlight the hovered node and its direct neighbors; dim everything else
- Cytoscape approach: on `mouseover node[type="cluster"]`, add class `highlighted` to the node + its connected edges + their target comment nodes; add class `dimmed` to everything else. Restore on `mouseout`.
- CSS classes:
  - `.highlighted` cluster node: increase shadow-blur, slightly lighter fill
  - `.dimmed` node/edge: `opacity: 0.15`
- Cursor: `pointer` on cluster hover, `default` otherwise (`cy.container().style.cursor`)

**Selected state (after click):**
- The clicked cluster node stays visually distinct while the panel is open — add class `selected` on open, remove on panel close
- `.selected`: border ring (`border-width: 3`, `border-color: #fff`, `border-opacity: 0.9`)

**Responsive canvas:**
- On `window.resize`, call `cy.resize()` then `cy.fit()` to re-fill the container

Implementation notes:
- Cytoscape's class system (`node.addClass`, `node.removeClass`) is the right tool here — do not manipulate styles directly
- Batch the class adds in a single `cy.batch()` call to avoid multiple redraws on hover
- The dimming effect is the most "Obsidian" part — it draws the eye to the hovered cluster and its comments

Acceptance:
- [ ] Hovering a cluster node highlights it and its comment nodes; everything else dims
- [ ] Moving off the node fully restores all node/edge opacity
- [ ] The selected cluster node has a visible ring while the panel is open
- [ ] Resizing the browser window resizes and refits the graph
- [ ] No console errors on hover, click, or resize
