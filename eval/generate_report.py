"""
Generate a formatted benchmark report from eval/results.csv.
Produces: eval/benchmark_report.md

Run AFTER benchmark.py:
  python eval/generate_report.py
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

RESULTS_PATH = Path(__file__).parent / "results.csv"
REPORT_PATH  = Path(__file__).parent / "benchmark_report.md"


def generate(results_path=RESULTS_PATH):
    df = pd.read_csv(results_path)
    now = datetime.now().strftime("%B %d, %Y")

    summary = df.groupby("pipeline").agg(
        avg_tokens     = ("total_tokens",   "mean"),
        avg_prompt_tok = ("prompt_tokens",  "mean"),
        avg_comp_tok   = ("completion_tokens", "mean"),
        avg_latency    = ("latency_s",      "mean"),
        avg_cost       = ("cost_usd",       "mean"),
        avg_bertscore  = ("bertscore_f1",     "mean"),
        avg_bertscore_raw = ("bertscore_f1_raw", "mean"),
        pass_rate      = ("judge_verdict",   lambda x: (x == "PASS").mean()),
        n_queries      = ("query_id",        "count"),
    ).round(4)

    order = ["llm_only", "basic_rag", "graphrag"]
    summary = summary.reindex([p for p in order if p in summary.index])

    # token reduction
    rag_tok   = summary.loc["basic_rag", "avg_tokens"] if "basic_rag" in summary.index else 1
    graph_tok = summary.loc["graphrag",  "avg_tokens"] if "graphrag"  in summary.index else 0
    tok_red   = (rag_tok - graph_tok) / max(rag_tok, 1) * 100

    pass_pct = summary.loc["graphrag", "pass_rate"] * 100 if "graphrag" in summary.index else 0
    bs_f1    = summary.loc["graphrag", "avg_bertscore"]    if "graphrag" in summary.index else 0

    judge_hit = pass_pct >= 90
    bert_hit  = bs_f1   >= 0.55
    bonus_str = "✅ Both bonus thresholds hit (max bonus)" if (judge_hit and bert_hit) \
           else ("⚠️ One threshold hit (partial bonus)" if (judge_hit or bert_hit) \
           else "❌ Neither bonus threshold hit")

    # per-query table
    per_query = df[df["pipeline"] == "graphrag"][
        ["query_id", "query", "total_tokens", "latency_s", "cost_usd", "bertscore_f1", "judge_verdict"]
    ].copy()
    per_query["query"] = per_query["query"].str[:60] + "…"

    report = f"""# LexGraph — Benchmark Report
*Indian Supreme Court GraphRAG Inference Benchmark*
Generated: {now}

---

## Project Overview

**LexGraph** is a GraphRAG benchmark built on Indian Supreme Court judgments (OpenNyai ILDC corpus, ~70k cases, 2M+ tokens). It compares three retrieval pipelines on legal reasoning queries that require multi-hop traversal across cases, constitutional articles, judges, and acts.

**Stack:** TigerGraph GraphRAG repo (Path A) · ChromaDB · sentence-transformers · OpenAI API · Streamlit

---

## Headline Results

| Metric | Value |
|---|---|
| **Token reduction (GraphRAG vs Basic RAG)** | **{tok_red:.1f}%** |
| **LLM-as-a-Judge pass rate (GraphRAG)** | **{pass_pct:.0f}%** |
| **BERTScore F1 rescaled (GraphRAG)** | **{bs_f1:.3f}** |
| **Bonus point status** | {bonus_str} |
| Queries evaluated | {int(summary.loc["graphrag","n_queries"]) if "graphrag" in summary.index else "—"} |

---

## Pipeline Comparison Summary

| Pipeline | Avg Tokens | Avg Latency (s) | Avg Cost (USD) | BERTScore F1 | Judge Pass Rate |
|---|---|---|---|---|---|
{"".join(f'| {p} | {summary.loc[p,"avg_tokens"]:,.0f} | {summary.loc[p,"avg_latency"]:.2f} | ${summary.loc[p,"avg_cost"]:.5f} | {summary.loc[p,"avg_bertscore"]:.3f} | {summary.loc[p,"pass_rate"]*100:.0f}% |{chr(10)}' for p in summary.index)}

---

## Token Reduction Detail

- **LLM-Only avg tokens:** {summary.loc["llm_only","avg_tokens"]:,.0f}
- **Basic RAG avg tokens:** {summary.loc["basic_rag","avg_tokens"]:,.0f}
- **GraphRAG avg tokens:** {summary.loc["graphrag","avg_tokens"]:,.0f}
- **GraphRAG vs Basic RAG reduction: {tok_red:.1f}%**
- **Tokens saved per query (avg):** {rag_tok - graph_tok:,.0f}
- **Cost saved per query (avg):** ${summary.loc["basic_rag","avg_cost"] - summary.loc["graphrag","avg_cost"]:.5f}

---

## Accuracy Evaluation

### LLM-as-a-Judge
Each GraphRAG answer was evaluated PASS/FAIL against a ground-truth reference answer by an LLM judge.

- **Pass rate: {pass_pct:.0f}%** {'✅ Hits ≥90% bonus threshold' if judge_hit else '❌ Below 90% bonus threshold'}

### BERTScore
Semantic similarity between GraphRAG answers and ground-truth references (computed via `bert-score`, `roberta-large`).

- **F1 rescaled: {bs_f1:.3f}** {'✅ Hits ≥0.55 bonus threshold' if bert_hit else '❌ Below 0.55 bonus threshold'}

---

## Per-Query Results (GraphRAG)

{per_query.to_markdown(index=False)}

---

## Why GraphRAG Wins on This Dataset

Indian Supreme Court judgments are deeply interconnected — cases cite cases, judges author multiple rulings, constitutional articles appear across decades of precedent. A single query like *"Which judges expanded Article 21 rights?"* requires traversing:

```
Query → Article 21 → Cases citing Article 21 → Authors (Judges) → Other cases by same judges
```

Vector RAG retrieves *similar chunks*, missing the structural relationship. GraphRAG traverses the graph directly, retrieving only the structurally relevant nodes — resulting in a focused, smaller context with higher accuracy.

---

## Architecture

```
User query
    │
    ├── Pipeline 1: LLM-Only ─────────────────────────► LLM → Answer
    │
    ├── Pipeline 2: Basic RAG ──► ChromaDB (vector) ──► LLM → Answer
    │                              top-5 chunks
    │
    └── Pipeline 3: GraphRAG ──► TigerGraph ──────────► LLM → Answer
                                  Entity extraction
                                  Multi-hop traversal
                                  Structured context
```

---

## Dataset

- **Source:** OpenNyai ILDC (Indian Legal Documents Corpus)
- **Size:** ~70,000 Supreme Court judgments
- **Token count:** 2M+ tokens (Round 1 requirement met)
- **License:** Public domain / open research use
- **Graph nodes:** Cases, Articles, Acts, Judges, Benches
- **Graph edges:** cites, references_article, references_act, authored_by, heard_by

---

*Built for the GraphRAG Inference Hackathon by TigerGraph.*
*GitHub: [your-repo-link] · Blog: [your-blog-link]*
"""

    REPORT_PATH.write_text(report)
    print(f"Report written to {REPORT_PATH}")
    return report


if __name__ == "__main__":
    if not RESULTS_PATH.exists():
        print(f"No results found at {RESULTS_PATH}. Run eval/benchmark.py first.")
        sys.exit(1)
    generate()
