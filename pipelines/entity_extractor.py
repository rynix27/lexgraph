"""
LLM-based entity extractor for legal queries.
Extracts: cases, articles, acts, legal concepts, judges.
Returns structured data used by GraphRAG pipeline for richer traversal.
"""

import json
from .base import llm_call, get_llm_client

EXTRACT_SYSTEM = """You are a legal entity extractor for Indian Supreme Court queries.
Extract all legal entities from the query and return ONLY valid JSON, no markdown.

Output format:
{
  "articles": ["21", "14", "19"],
  "cases": ["Maneka Gandhi v Union of India", "Puttaswamy"],
  "acts": ["Prevention of Money Laundering Act", "AFSPA"],
  "concepts": ["right to privacy", "basic structure doctrine"],
  "judges": ["Justice Bhagwati", "Justice Krishna Iyer"],
  "temporal": {"after": 2017, "before": null}
}

Rules:
- articles: constitutional article numbers only (strings)
- cases: partial names are fine, include both parties if mentioned
- concepts: legal doctrines, principles, tests
- temporal: extract year constraints if mentioned (e.g. "after 2017", "since independence")
- If nothing found in a field, use empty list / null
- Output ONLY the JSON object"""


_client = None

def get_client():
    global _client
    if _client is None:
        _client = get_llm_client()
    return _client


def extract_entities(query: str) -> dict:
    """Extract structured legal entities from a natural language query."""
    try:
        raw, _, _ = llm_call(get_client(), EXTRACT_SYSTEM, query)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        entities = json.loads(raw)
    except Exception:
        # fallback to regex if LLM fails
        import re
        entities = {
            "articles": list(set(re.findall(r"Article\s+(\d+[A-Z]?)", query))),
            "cases": [],
            "acts": [],
            "concepts": [],
            "judges": [],
            "temporal": {"after": None, "before": None},
        }

    # always ensure all keys exist
    entities.setdefault("articles", [])
    entities.setdefault("cases", [])
    entities.setdefault("acts", [])
    entities.setdefault("concepts", [])
    entities.setdefault("judges", [])
    entities.setdefault("temporal", {"after": None, "before": None})

    return entities


def entities_to_graph_hops(entities: dict) -> list[dict]:
    """
    Convert extracted entities into a list of graph traversal hops.
    Each hop describes a node type + value that will be looked up in TigerGraph.
    This is what powers the graph visualization.
    """
    hops = []

    for art in entities["articles"]:
        hops.append({"type": "Article", "id": f"Art_{art}", "label": f"Article {art}", "color": "#7F77DD"})

    for case in entities["cases"]:
        hops.append({"type": "Case", "id": case, "label": case[:40], "color": "#1D9E75"})

    for act in entities["acts"]:
        hops.append({"type": "Act", "id": act, "label": act[:40], "color": "#D85A30"})

    for concept in entities["concepts"]:
        hops.append({"type": "Concept", "id": concept, "label": concept[:40], "color": "#BA7517"})

    return hops
