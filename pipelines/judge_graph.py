"""
Judge-aware graph traversal for queries about specific judges or benches.

Extends the GraphRAG pipeline with:
  - Judge vertex lookup (authored_by edges)
  - Bench composition queries (heard_by edges)
  - Cross-judge comparison (which judges ruled differently on the same article)

This module is called by graphrag.py when the entity extractor finds judge names.
"""

import os
from typing import Optional


def query_judge_network(conn, judges: list[str], articles: list[str]) -> str:
    """
    Multi-hop: Judge → Cases they authored → Articles those cases cite.
    Returns a structured context string for the LLM.
    Uses runInstalledQuery only — safe for TigerGraph Savanna.
    (conn.gsql INTERPRET QUERY requires special permissions not available on cloud.)
    """
    if not judges:
        return ""

    lines = [f"Judge network traversal: {', '.join(judges)}\n"]

    for judge_name in judges[:3]:
        try:
            rows = conn.runInstalledQuery(
                "get_cases_by_judge",
                params={"judge_name": judge_name, "limit": 10},
            )
            if rows and isinstance(rows, list):
                lines.append(f"\nJudge: {judge_name}")
                for row in rows[:5]:
                    if isinstance(row, dict):
                        case = row.get("attributes", row)
                        lines.append(f"  → {case.get('title', 'Unknown')} ({case.get('year', '')})")
        except Exception as e:
            # Installed query not yet deployed — skip gracefully.
            # Run data/ingest.py to install queries first.
            lines.append(f"\nNote: Judge lookup unavailable for {judge_name} ({e})")

    return "\n".join(lines)


def build_judge_schema_extension() -> str:
    """
    Returns GSQL to add Judge and Bench vertices + authored_by / heard_by edges.
    Safe to run multiple times (IF NOT EXISTS style).
    """
    return """
        CREATE VERTEX IF NOT EXISTS Judge (
            PRIMARY_ID judge_id STRING,
            name       STRING,
            tenure_start INT,
            tenure_end   INT
        ) WITH primary_id_as_attribute="true"

        CREATE VERTEX IF NOT EXISTS Bench (
            PRIMARY_ID bench_id STRING,
            size       INT,
            composition STRING
        ) WITH primary_id_as_attribute="true"

        CREATE DIRECTED EDGE IF NOT EXISTS authored_by (FROM Case, TO Judge)
        CREATE DIRECTED EDGE IF NOT EXISTS heard_by    (FROM Case, TO Bench)
        CREATE DIRECTED EDGE IF NOT EXISTS sat_on      (FROM Judge, TO Bench)
    """


def extract_judges_from_text(text: str) -> list[str]:
    """
    Heuristic extraction of judge names from case text.
    Used during ingest to populate authored_by edges.
    """
    import re
    # Matches: "Justice X", "Hon'ble Mr. Justice X Y", "J. X"
    patterns = [
        r"Justice\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})",
        r"Hon'ble\s+(?:Mr\.|Ms\.)?\s*Justice\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})",
        r"\bJ\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
    ]
    judges = set()
    for p in patterns:
        for m in re.finditer(p, text[:3000]):  # only header/first page
            name = m.group(1).strip()
            if len(name) > 3 and not any(stop in name for stop in ["Court", "India", "Union", "State"]):
                judges.add(name)
    return list(judges)[:5]
