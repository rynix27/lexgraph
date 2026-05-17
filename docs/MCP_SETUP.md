# TigerGraph MCP Setup (Optional Power Feature)

The hackathon brief mentions TigerGraph MCP as a tip for building faster.
This lets you connect TigerGraph directly to Cursor or VS Code Copilot and query your graph with natural language during development — no GSQL needed.

## What it enables

- Natural language → GSQL during development ("show me all cases citing Article 21 in 3 hops")
- Fast schema iteration without writing boilerplate
- Debug graph queries interactively while building

## Setup (5 minutes)

### 1. Install the TigerGraph MCP server

```bash
git clone https://github.com/tigergraph/tigergraph-mcp.git
cd tigergraph-mcp
pip install -e .
```

### 2. Configure (add to your .env)

```env
TG_MCP_HOST=https://your-instance.i.tgcloud.io
TG_MCP_GRAPH=LexGraph
TG_MCP_USERNAME=tigergraph
TG_MCP_PASSWORD=your-password
```

### 3. Use with Cursor

In Cursor Settings → MCP Servers → Add:
```json
{
  "name": "tigergraph",
  "command": "python",
  "args": ["-m", "tigergraph_mcp"],
  "env": {
    "TG_HOST": "https://your-instance.i.tgcloud.io",
    "TG_GRAPH": "LexGraph"
  }
}
```

Now you can ask Cursor: *"Query the graph for all judges who authored cases referencing Article 21 after 1990"* and it writes the GSQL for you.

### 4. Use programmatically (in your pipeline)

```python
# Instead of writing raw GSQL, use the MCP client
from tigergraph_mcp import TigerGraphMCP

mcp = TigerGraphMCP(host=os.environ["TG_HOST"], graph="LexGraph")
result = mcp.query("Find all cases that cite Article 21 with expansion holdings, authored after 1980")
# Returns structured results ready to pass to your LLM
```

## Why this helps the hackathon submission

If you mention MCP usage in your demo video and blog post, it signals you explored the full TigerGraph toolchain — which the judges explicitly called out in the brief as a differentiator.

> "Just a tip: you can connect TigerGraph directly to your AI coding tools (Cursor, VS Code Copilot) using MCP and build with natural language." — Hackathon brief

Even a 30-second mention in your video ("I used TigerGraph MCP during development to iterate on graph queries faster") covers this.

## Links

- MCP repo: https://github.com/tigergraph/tigergraph-mcp
- Hackathon guide: https://www.notion.so/Build-Faster-with-MCP-daffc4e1c08c83ebb4f481e8a97e1468
