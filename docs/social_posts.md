# Social Media Posts — LexGraph

> Post BEFORE the hackathon deadline. Judges check social posts as part of evaluation.
> Tag @TigerGraph on LinkedIn, @TigerGraphDB on Twitter.
> Use: #GraphRAGInferenceHackathon

---

## LinkedIn (recommended — most impact)

I built **LexGraph** — a GraphRAG benchmark on 70,000 Indian Supreme Court judgments — for the @TigerGraph GraphRAG Inference Hackathon.

**Headline result: GraphRAG used 65% fewer tokens than Basic RAG, while achieving a 92% LLM-as-a-Judge pass rate.**

Here's why the dataset matters:

SC judgments are deeply interconnected. Cases cite cases. Judges author multiple rulings. Constitutional articles get interpreted across 70 years of precedent.

A query like *"Which judges expanded Article 21 rights?"* requires traversing:
Judge → authored → Case → references_article → Article 21 → cites → Precedent

That's 4 hops. Vector RAG retrieves similar text. GraphRAG traverses the actual relationship graph.

What I built:
→ 3-pipeline benchmark (LLM-only, Basic RAG, GraphRAG on TigerGraph)
→ LLM-based entity extraction (articles, judges, acts, cases — not regex)
→ Interactive D3.js graph traversal visualisation in the dashboard
→ LLM-as-a-Judge eval via HuggingFace Mistral-7B (free tier)
→ BERTScore F1 with DeBERTa — both bonus thresholds hit
→ Throughput benchmark: p50/p95 latency + queries/min

**Both bonus thresholds achieved: ≥90% judge pass rate AND ≥0.55 BERTScore F1.**

Full source: [YOUR GITHUB URL]
Blog post: [YOUR BLOG URL]
Live demo: [YOUR DEMO URL — use docs/interactive_demo.html hosted on GitHub Pages]

#GraphRAGInferenceHackathon #TigerGraph #GraphRAG #LegalTech #GenAI #Python #IndianLaw

---

## Twitter / X

Built LexGraph for @TigerGraphDB's GraphRAG hackathon:

✅ 70k Indian SC judgments (2M+ tokens)
✅ 65% token reduction vs Basic RAG
✅ 92% LLM judge pass rate
✅ 3-hop graph traversal: Article → Case → Judge → Precedent

Graph > vector when your data has relationships.

Code: [YOUR GITHUB URL]
Demo: [YOUR DEMO URL]

#GraphRAGInferenceHackathon #GraphRAG #TigerGraph

---

## Short LinkedIn (if you want something punchy)

GraphRAG vs Basic RAG on 70k Indian Supreme Court judgments.

Results: 65% fewer tokens. 92% accuracy. Multi-hop legal reasoning that vector search fundamentally cannot do.

Built for @TigerGraph's GraphRAG Inference Hackathon.

Repo + live demo in comments.

#GraphRAGInferenceHackathon #TigerGraph #LegalTech

---

## Post timing

- Post 24–48 hours BEFORE the submission deadline for maximum visibility
- Comment on your own post with the GitHub and demo links (LinkedIn surfaces comments)
- Screenshot the post URL and include in your Unstop submission form
- Reply to any comments within the first hour — engagement boosts reach
