"""
graph_viz.py
Generates a self-contained HTML string that renders an animated
force-directed graph using D3.js, showing the multi-hop traversal
as nodes light up one by one.

Used by the dashboard via st.components.v1.html()
"""

import json


# Node colors by type
NODE_COLORS = {
    "Article":  "#7F77DD",   # purple
    "Case":     "#1D9E75",   # teal
    "Act":      "#D85A30",   # coral
    "Concept":  "#BA7517",   # amber
    "Judge":    "#378ADD",   # blue
    "Query":    "#E24B4A",   # red — the seed node
}

NODE_RADIUS = {
    "Query":   22,
    "Article": 18,
    "Case":    16,
    "Act":     14,
    "Concept": 13,
    "Judge":   13,
}


def build_graph_data(query: str, entities: dict, retrieved_cases: list = None) -> dict:
    """
    Build a D3-compatible {nodes, links} graph from extracted entities.
    The query itself is the root node. Entities radiate outward.
    Retrieved cases are shown as a second hop from the article/act nodes.
    """
    nodes = []
    links = []
    seen  = set()

    def add_node(id_, label, type_):
        if id_ not in seen:
            nodes.append({
                "id":     id_,
                "label":  label[:35] + ("…" if len(label) > 35 else ""),
                "type":   type_,
                "color":  NODE_COLORS.get(type_, "#888"),
                "radius": NODE_RADIUS.get(type_, 14),
            })
            seen.add(id_)

    # root: the query
    root_id = "query_root"
    add_node(root_id, query[:45] + "…" if len(query) > 45 else query, "Query")

    # hop 1: articles
    for art in (entities.get("articles") or [])[:4]:
        nid = f"Art_{art}"
        add_node(nid, f"Article {art}", "Article")
        links.append({"source": root_id, "target": nid, "label": "queries"})

    # hop 1: concepts
    for c in (entities.get("concepts") or [])[:3]:
        nid = f"Concept_{c[:20]}"
        add_node(nid, c, "Concept")
        links.append({"source": root_id, "target": nid, "label": "involves"})

    # hop 1: judges
    for j in (entities.get("judges") or [])[:2]:
        nid = f"Judge_{j[:20]}"
        add_node(nid, j, "Judge")
        links.append({"source": root_id, "target": nid, "label": "by"})

    # hop 1: acts
    for act in (entities.get("acts") or [])[:3]:
        nid = f"Act_{act[:20]}"
        add_node(nid, act, "Act")
        links.append({"source": root_id, "target": nid, "label": "under"})

    # hop 2: retrieved cases link back to articles/concepts
    if retrieved_cases:
        article_nodes = [n["id"] for n in nodes if n["type"] == "Article"]
        for i, case in enumerate(retrieved_cases[:6]):
            nid = f"Case_{i}"
            add_node(nid, case.get("title", f"Case {i}"), "Case")
            # connect to nearest article node, or root if none
            anchor = article_nodes[i % len(article_nodes)] if article_nodes else root_id
            links.append({"source": anchor, "target": nid, "label": "cites"})

    # hop 2: cases mentioned in query
    for i, case in enumerate((entities.get("cases") or [])[:3]):
        nid = f"QueryCase_{i}"
        add_node(nid, case, "Case")
        links.append({"source": root_id, "target": nid, "label": "involves"})

    return {"nodes": nodes, "links": links}


def render_graph_html(query: str, entities: dict,
                      retrieved_cases: list = None,
                      height: int = 480) -> str:
    """Return self-contained HTML with animated D3 force-directed graph."""

    graph_data = build_graph_data(query, entities, retrieved_cases)
    graph_json = json.dumps(graph_data)
    colors_json = json.dumps(NODE_COLORS)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: transparent; font-family: system-ui, sans-serif; overflow: hidden; }}
  #graph {{ width: 100%; height: {height}px; }}
  .node circle {{ stroke-width: 2px; stroke: white; cursor: pointer; transition: opacity 0.3s; }}
  .node text {{ font-size: 11px; fill: #333; pointer-events: none; text-anchor: middle; }}
  .link {{ stroke: #ccc; stroke-opacity: 0.6; stroke-width: 1.5px; fill: none; }}
  .link-label {{ font-size: 9px; fill: #999; }}
  .legend {{ position: absolute; top: 12px; right: 12px; background: rgba(255,255,255,0.92);
             border-radius: 8px; padding: 10px 14px; font-size: 11px; border: 1px solid #e5e5e5; }}
  .legend-item {{ display: flex; align-items: center; gap: 6px; margin: 3px 0; }}
  .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}
  .hop-counter {{ position: absolute; bottom: 12px; left: 16px; font-size: 12px; color: #666; }}
  @media (prefers-color-scheme: dark) {{
    .node text {{ fill: #ddd; }}
    .legend {{ background: rgba(30,30,30,0.92); border-color: #444; color: #ddd; }}
    .hop-counter {{ color: #aaa; }}
  }}
</style>
</head>
<body>
<div style="position:relative">
  <svg id="graph"></svg>
  <div class="legend" id="legend"></div>
  <div class="hop-counter" id="hop-counter">Initialising traversal...</div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<script>
const graphData  = {graph_json};
const nodeColors = {colors_json};
const W = document.getElementById('graph').parentElement.offsetWidth || 700;
const H = {height};

const svg = d3.select('#graph')
  .attr('width', W).attr('height', H);

const defs = svg.append('defs');
defs.append('marker')
  .attr('id', 'arrowhead')
  .attr('viewBox', '-0 -5 10 10')
  .attr('refX', 20).attr('refY', 0)
  .attr('orient', 'auto').attr('markerWidth', 6).attr('markerHeight', 6)
  .append('path').attr('d', 'M 0,-5 L 10,0 L 0,5').attr('fill', '#ccc');

const g = svg.append('g');

svg.call(d3.zoom()
  .scaleExtent([0.4, 3])
  .on('zoom', e => g.attr('transform', e.transform)));

const sim = d3.forceSimulation(graphData.nodes)
  .force('link', d3.forceLink(graphData.links).id(d => d.id).distance(d => {{
    if (d.source.type === 'Query') return 140;
    return 100;
  }}))
  .force('charge', d3.forceManyBody().strength(-320))
  .force('center', d3.forceCenter(W / 2, H / 2))
  .force('collision', d3.forceCollide(d => d.radius + 12));

const link = g.append('g').selectAll('line')
  .data(graphData.links).join('line')
  .attr('class', 'link')
  .attr('marker-end', 'url(#arrowhead)');

const node = g.append('g').selectAll('g')
  .data(graphData.nodes).join('g')
  .attr('class', 'node')
  .call(d3.drag()
    .on('start', (e, d) => {{ if (!e.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }})
    .on('drag',  (e, d) => {{ d.fx = e.x; d.fy = e.y; }})
    .on('end',   (e, d) => {{ if (!e.active) sim.alphaTarget(0); d.fx = null; d.fy = null; }}));

node.append('circle')
  .attr('r', d => d.radius)
  .attr('fill', d => d.color)
  .attr('opacity', 0);

node.append('text')
  .attr('dy', d => d.radius + 13)
  .text(d => d.label)
  .attr('opacity', 0);

sim.on('tick', () => {{
  link
    .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
    .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
  node.attr('transform', d => `translate(${{d.x}},${{d.y}})`);
}});

// Animate nodes appearing one by one (traversal effect)
const counter = document.getElementById('hop-counter');
const hopLabels = ['Seeding query...', 'Extracting entities...', 'Traversing graph...', 'Finding precedents...', 'Ranking by relevance...', 'Context ready'];

let i = 0;
function revealNext() {{
  if (i >= graphData.nodes.length) {{
    counter.textContent = `Traversal complete — ${{graphData.nodes.length}} nodes, ${{graphData.links.length}} edges`;
    // pulse the root node
    d3.selectAll('.node circle').filter((d,j) => j===0)
      .transition().duration(600).attr('r', d => d.radius * 1.3)
      .transition().duration(400).attr('r', d => d.radius);
    return;
  }}
  const nd = d3.selectAll('.node').filter((d,j) => j === i);
  nd.select('circle').transition().duration(350).attr('opacity', 1);
  nd.select('text').transition().duration(350).attr('opacity', 1);
  counter.textContent = hopLabels[Math.min(i, hopLabels.length - 1)] + ` (${{i+1}}/${{graphData.nodes.length}})`;
  i++;
  setTimeout(revealNext, i === 1 ? 300 : 180);
}}
setTimeout(revealNext, 600);

// Legend
const seen = {{}};
const legendEl = document.getElementById('legend');
legendEl.innerHTML = '<div style="font-weight:600;margin-bottom:6px;font-size:12px">Node types</div>';
graphData.nodes.forEach(n => {{
  if (!seen[n.type]) {{
    seen[n.type] = true;
    legendEl.innerHTML += `<div class="legend-item">
      <div class="legend-dot" style="background:${{n.color}}"></div>
      <span>${{n.type}}</span></div>`;
  }}
}});
</script>
</body></html>"""
