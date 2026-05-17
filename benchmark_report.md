# LexGraph — Benchmark Report
**GraphRAG Inference Hackathon by TigerGraph**

## Dataset

- **Domain:** Indian Supreme Court Judgments
- **Source:** OpenNyAI ILDC corpus (indianlegalresearch.org / HuggingFace: `opennyaiorg/ILDC_multi`)
- **Round 1 subset:** ~6,000 cases ingested (sampled from the full 70k corpus for development)
- **Estimated tokens in ingested subset:** ~3.8M (exceeds 2M Round 1 requirement)
- **Round 2 plan:** Scale to full 70k case corpus (~50–100M tokens) using provided Gemini API credits

## Pipeline Architecture

| Pipeline | Retrieval | Context sent to LLM |
|---|---|---|
| LLM-Only | None | Query only |
| Basic RAG | ChromaDB top-5 chunks, ~800 chars each | ~1,500 tokens of raw text |
| GraphRAG | TigerGraph multi-hop (3 hops, top-3 nodes), compressed | ~500 tokens of structured entity context |

**Why GraphRAG uses fewer tokens:** Graph traversal returns structured relationship data
(Case → Article → Judge chains) rather than raw text chunks. Combined with entity-enriched
retrieval (fewer false-positive chunks) and a hard context compression step, GraphRAG
delivers more targeted context at ~60–70% lower token cost.

## Benchmark Results

### Token Usage & Cost

| Pipeline | Avg Prompt Tokens | Avg Completion Tokens | Avg Total Tokens | Token Δ vs Basic RAG | Avg Cost (USD) |
|---|---|---|---|---|---|
| LLM-Only | ~50 | ~120 | ~170 | −93% | $0.000025 |
| Basic RAG | ~1,400 | ~200 | ~1,600 | baseline | $0.00030 |
| **GraphRAG** | **~520** | **~150** | **~670** | **−58%** | **$0.000095** |

> **GraphRAG reduces tokens by ~58% vs Basic RAG** while delivering higher accuracy
> on multi-hop legal reasoning queries. Cost reduction is proportional.

### Throughput (5 Concurrent Queries)

| Pipeline | p50 Latency | p95 Latency | QPM |
|---|---|---|---|
| LLM-Only | 1.2s | 1.5s | 280 |
| Basic RAG | 3.6s | 4.2s | 92 |
| GraphRAG | 22s | 25s | 14 |

> GraphRAG latency is higher due to multi-hop graph traversal and entity extraction.
> This is a known tradeoff for complex relational queries; latency is bounded and
> acceptable for legal research workloads where precision matters more than throughput.

### Accuracy

| Pipeline | BERTScore F1 (raw, roberta-large) | BERTScore F1 (rescaled) | LLM-as-Judge Pass Rate |
|---|---|---|---|
| LLM-Only | 0.849 | 0.056 | 70% |
| Basic RAG | 0.851 | 0.069 | 75% |
| **GraphRAG** | **0.874** | **0.213** | **80%** |

> **Bonus threshold status:**
> - LLM-as-Judge ≥ 90%: ❌ Not yet hit — ongoing tuning (see below)
> - BERTScore rescaled ≥ 0.55: ❌ Not yet hit — see tuning roadmap

> **Note on accuracy tuning:** The hackathon README states that "GraphRAG requires
> iterative tuning to ensure high answer accuracy" and that teams should adjust
> chunking strategy, hop depth, LLM selection, and prompt design. Our current results
> show GraphRAG outperforming both baselines on both accuracy metrics, with tuning
> ongoing for Round 2 to hit the bonus thresholds.

## Key Findings

### Why GraphRAG wins on this dataset

Indian Supreme Court judgments are deeply relational: cases cite cases, judges author
dozens of rulings, constitutional articles recur across decades of precedent. A query
like *"Which judges expanded Article 21 rights?"* requires traversing:

```
Query → Article 21 → Cases citing Article 21 → Authors (Judges) → Other cases by same judges
```

Vector RAG retrieves *similar chunks*, missing this structural relationship entirely.
GraphRAG traverses the graph directly, retrieving only the structurally relevant nodes —
resulting in a focused, smaller context with higher accuracy on relational queries.

### Token reduction mechanism

```
Basic RAG:   query → embed → top-5 chunks (~800 chars each) → ~1,500 prompt tokens
GraphRAG:    query → entity extract → graph traversal (3 hops, top-3 nodes)
                  → compress to structured summary (~300 chars per node)
                  → ~500 prompt tokens
```

Reduction = 1 − (670 / 1,600) ≈ **58%**

### Accuracy advantage

On multi-hop legal reasoning queries (the benchmark set), GraphRAG outperforms Basic RAG
because graph traversal is semantically aware of entity relationships, not just textual
similarity. The LLM receives named cases, articles, and judges in structured form rather
than raw paragraph fragments that may not contain the relational answer.

## Accuracy Evaluation Methodology

- **BERTScore:** `bert-score` library, `roberta-large` model. Computes F1 between
  GraphRAG answers and ground-truth references. Rescaling baseline: 0.84 (standard
  roberta-large random-pair baseline).
- **LLM-as-Judge:** Gemini grades each answer PASS/FAIL against ground-truth reference,
  with explicit criteria (correct case names, correct legal principle, no hallucinations).
- **10 benchmark queries** targeting multi-hop legal reasoning: citation chains, judge
  contribution tracing, doctrine evolution across decades.

## Infrastructure

- **Graph DB:** TigerGraph Savanna (Cloud, US-EAST-1)
- **Vector DB:** ChromaDB (local persistent, fallback)
- **Embeddings:** all-MiniLM-L6-v2 (sentence-transformers)
- **LLM:** Gemini 2.5 Flash (via OpenAI-compatible API)
- **GraphRAG:** TigerGraph GraphRAG repo, Path A (REST API, Docker)
- **Evaluation:** bert-score (roberta-large) + Gemini LLM-as-Judge

## Tuning Roadmap (Round 2)

For Round 2 (50–100M token scale), planned improvements to hit bonus thresholds:

1. **Chunk size tuning:** Test chunk sizes 256, 512, 1024 tokens during ingest
2. **Hop depth sweep:** Benchmark GRAPHRAG_HOPS in {2, 3, 4} on accuracy vs token tradeoff
3. **Retriever selection:** Switch from Hybrid Search to Community retriever for broad doctrine queries
4. **Prompt refinement:** Add chain-of-thought instruction to improve judge pass rate
5. **Full corpus ingestion:** 70k cases → richer graph → better multi-hop paths
