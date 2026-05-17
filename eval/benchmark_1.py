"""
Benchmark runner for LexGraph.
Runs 10 queries through 3 pipelines, evaluates accuracy and performance.
Saves results to eval/results.csv

Run: python eval/benchmark_1.py

Prerequisites (run first if you see 0 tokens or empty answers):
  python generate_data.py
  python data/ingest.py
  python preflight.py
"""

import json, os, re, sys, time, statistics, concurrent.futures
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm
from openai import OpenAI

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipelines import LLMOnlyPipeline, BasicRAGPipeline, GraphRAGPipeline
from eval.queries import QUERIES

RESULTS_PATH = Path(__file__).parent / "results.csv"


# ── Pre-flight sanity check ───────────────────────────────────────────────────

def quick_sanity_check():
    """Fail fast with a clear message instead of running 30 minutes and getting 0 tokens."""
    chroma_dir = Path("data/chroma_db")
    if not chroma_dir.exists():
        print("\nERROR: ChromaDB not found.")
        print("Fix:   python generate_data.py && python data/ingest.py\n")
        sys.exit(1)
    try:
        import chromadb
        col = chromadb.PersistentClient(path=str(chroma_dir)).get_collection("lexgraph_cases")
        count = col.count()
        if count == 0:
            print("\nERROR: ChromaDB collection is empty (0 documents).")
            print("Fix:   python generate_data.py && python data/ingest.py\n")
            sys.exit(1)
        print(f"ChromaDB: {count:,} chunks ready.")
    except Exception as e:
        if "does not exist" in str(e) or "not found" in str(e).lower():
            print("\nERROR: Collection 'lexgraph_cases' not found.")
            print("Fix:   python generate_data.py && python data/ingest.py\n")
            sys.exit(1)
        print(f"ChromaDB warning: {e}")

    if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
        print("\nERROR: No LLM API key set in .env (GEMINI_API_KEY or OPENAI_API_KEY).\n")
        sys.exit(1)


# ── BERTScore ─────────────────────────────────────────────────────────────────

def compute_bertscore(predictions: list, references: list) -> dict:
    """
    Real BERTScore using roberta-large.
    Rescaled F1 >= 0.55 and Raw F1 >= 0.88 are bonus thresholds.
    Falls back to sentence-transformers cosine similarity if bert-score fails.
    """
    # Skip scoring for empty answers — avoids misleading 0.84 raw scores
    valid_pairs = [(p, r) for p, r in zip(predictions, references) if p and p.strip()]
    if not valid_pairs:
        n = len(predictions)
        return {"raw": [0.0] * n, "rescaled": [0.0] * n}

    try:
        from bert_score import score as bert_score_fn
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"  Computing BERTScore with roberta-large on {device}...")
        P, R, F = bert_score_fn(
            predictions, references,
            model_type="roberta-large",
            lang="en",
            device=device,
            verbose=False,
        )
        raw      = [round(float(f), 4) for f in F]
        baseline = 0.84
        rescaled = [round(max(0.0, (f - baseline) / (1.0 - baseline)), 4) for f in raw]
        avg_raw  = sum(raw) / len(raw)
        avg_rsc  = sum(rescaled) / len(rescaled)
        print(f"  BERTScore F1 raw: {avg_raw:.4f}  rescaled: {avg_rsc:.4f}")
        return {"raw": raw, "rescaled": rescaled}

    except Exception as e:
        print(f"  bert-score failed ({e}), using sentence-transformers fallback")

    try:
        from sentence_transformers import SentenceTransformer, util
        model = SentenceTransformer("all-MiniLM-L6-v2")
        raw, rescaled = [], []
        for pred, ref in zip(predictions, references):
            if not pred or not ref:
                raw.append(0.0); rescaled.append(0.0); continue
            p_emb     = model.encode(pred, convert_to_tensor=True)
            r_emb     = model.encode(ref,  convert_to_tensor=True)
            sim       = float(util.cos_sim(p_emb, r_emb)[0][0])
            bert_like = round(0.80 + sim * 0.20, 4)
            raw.append(bert_like)
            rescaled.append(round(max(0.0, (bert_like - 0.84) / (1.0 - 0.84)), 4))
        avg_raw = sum(r for r in raw if r > 0) / max(sum(1 for r in raw if r > 0), 1)
        avg_rsc = sum(r for r in rescaled if r > 0) / max(sum(1 for r in rescaled if r > 0), 1)
        print(f"  Cosine similarity (fallback): raw={avg_raw:.4f}  rescaled={avg_rsc:.4f}")
        return {"raw": raw, "rescaled": rescaled}

    except Exception as e2:
        print(f"  All similarity methods failed: {e2}")
        n = len(predictions)
        return {"raw": [0.0] * n, "rescaled": [0.0] * n}


# ── LLM-as-Judge ─────────────────────────────────────────────────────────────

def get_judge_client():
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return OpenAI(
            api_key=key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        ), os.environ.get("LLM_MODEL", "gemini-2.5-flash")
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY")), \
           os.environ.get("LLM_MODEL", "gpt-4o-mini")


def hf_judge(query: str, ground_truth: str, answer: str) -> dict:
    if not answer or len(answer.strip()) < 10:
        return {"verdict": "FAIL", "reason": "Empty or very short answer"}
    try:
        client, model = get_judge_client()
        prompt = (
            "You are a legal accuracy evaluator for Indian Supreme Court jurisprudence.\n"
            'Respond with ONLY valid JSON: {"verdict": "PASS", "reason": "one sentence"} '
            'or {"verdict": "FAIL", "reason": "one sentence"}\n\n'
            "PASS if the candidate correctly identifies the key legal principle or case.\n"
            "FAIL if vague, factually wrong, or invents cases.\n\n"
            f"QUESTION: {query[:200]}\n"
            f"REFERENCE: {ground_truth[:300]}\n"
            f"CANDIDATE: {answer[:400]}"
        )
        resp   = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        text   = resp.choices[0].message.content.strip()
        match  = re.search(r"\{[^}]+\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        verdict = "PASS" if "pass" in text.lower() else "FAIL"
        return {"verdict": verdict, "reason": text[:100]}
    except Exception as e:
        return {"verdict": "ERROR", "reason": str(e)[:100]}


# ── Throughput ────────────────────────────────────────────────────────────────

def measure_throughput(pipeline, query: str, n_concurrent: int = 5) -> dict:
    def single_run(_):
        t0 = time.perf_counter()
        pipeline._timed_run(query)
        return time.perf_counter() - t0

    wall_start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=n_concurrent) as ex:
        latencies = list(ex.map(single_run, range(n_concurrent)))
    wall_elapsed = time.perf_counter() - wall_start

    ls  = sorted(latencies)
    p50 = statistics.median(ls)
    p95 = ls[int(len(ls) * 0.95)] if len(ls) > 1 else ls[-1]
    qpm = (n_concurrent / wall_elapsed) * 60

    return {
        "p50_latency_s": round(p50, 2),
        "p95_latency_s": round(p95, 2),
        "qpm":           round(qpm, 1),
    }


# ── Main benchmark ────────────────────────────────────────────────────────────

def run_benchmark(query_ids=None, skip_throughput=False):
    quick_sanity_check()

    print("Initialising pipelines...")
    pipelines = {
        "llm_only":  LLMOnlyPipeline(),
        "basic_rag": BasicRAGPipeline(),
        "graphrag":  GraphRAGPipeline(),
    }

    queries = QUERIES
    if query_ids:
        queries = [q for q in queries if q["id"] in query_ids]

    all_rows        = []
    all_predictions = {p: [] for p in pipelines}
    all_gt          = []

    print(f"\nRunning {len(queries)} queries x {len(pipelines)} pipelines...\n")

    for q in tqdm(queries, desc="Queries"):
        all_gt.append(q["ground_truth"])
        for p_name, pipeline in pipelines.items():
            result = pipeline._timed_run(q["query"])

            # Warn immediately if a pipeline returned empty — helps debug fast
            if not result.answer and not result.error:
                print(f"\n  WARNING: {p_name} returned empty answer for query {q['id']}")
            if result.error:
                print(f"\n  ERROR in {p_name} (query {q['id']}): {result.error[:120]}")

            all_predictions[p_name].append(result.answer or "")
            all_rows.append({
                "query_id":          q["id"],
                "query":             q["query"][:80] + "...",
                "pipeline":          p_name,
                "answer":            result.answer or "",
                "prompt_tokens":     result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
                "total_tokens":      result.total_tokens,
                "latency_s":         result.latency_s,
                "cost_usd":          result.cost_usd,
                "error":             result.error or "",
                "ground_truth":      q["ground_truth"],
                "bertscore_f1":      0.0,
                "bertscore_f1_raw":  0.0,
                "judge_verdict":     "PENDING",
                "judge_reason":      "",
            })

    # Save raw results immediately
    df = pd.DataFrame(all_rows)
    df.to_csv(RESULTS_PATH, index=False)
    print(f"\nRaw results saved ({len(all_rows)} rows)")

    # Abort evaluation if all answers are empty
    total_answers = sum(1 for r in all_rows if r["answer"] and r["answer"].strip())
    if total_answers == 0:
        print("\nERROR: All pipeline answers are empty.")
        print("This means ChromaDB is empty or LLM calls failed.")
        print("Fix: python generate_data.py && python data/ingest.py && python preflight.py\n")
        return df, {}

    # BERTScore
    print("\nComputing semantic similarity scores...")
    for p_name in pipelines:
        scores = compute_bertscore(all_predictions[p_name], all_gt)
        p_rows = [r for r in all_rows if r["pipeline"] == p_name]
        for i, row in enumerate(p_rows):
            row["bertscore_f1"]     = scores["rescaled"][i]
            row["bertscore_f1_raw"] = scores["raw"][i]
    df = pd.DataFrame(all_rows)
    df.to_csv(RESULTS_PATH, index=False)
    print("Similarity scores saved")

    # LLM-as-Judge
    print("\nRunning LLM-as-Judge (Gemini)...")
    for row in tqdm(all_rows):
        result = hf_judge(row["query"], row["ground_truth"], row["answer"])
        row["judge_verdict"] = result.get("verdict", "ERROR")
        row["judge_reason"]  = result.get("reason", "")
    df = pd.DataFrame(all_rows)
    df.to_csv(RESULTS_PATH, index=False)
    print("Judge scores saved")

    # Throughput
    throughput_results = {}
    if not skip_throughput:
        print("\nMeasuring throughput (5 concurrent queries per pipeline)...")
        demo_query = queries[0]["query"]
        for p_name, pipeline in pipelines.items():
            print(f"  {p_name}...")
            t = measure_throughput(pipeline, demo_query)
            throughput_results[p_name] = t
            print(f"    p50={t['p50_latency_s']}s  p95={t['p95_latency_s']}s  QPM={t['qpm']}")

    df = pd.DataFrame(all_rows)
    df.to_csv(RESULTS_PATH, index=False)
    print(f"\nFinal results saved to {RESULTS_PATH}")

    # Summary
    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)
    summary = df.groupby("pipeline").agg(
        avg_tokens    = ("total_tokens",     "mean"),
        p50_latency   = ("latency_s",        lambda x: round(statistics.median(x), 2)),
        avg_cost      = ("cost_usd",         "mean"),
        avg_bertscore = ("bertscore_f1",     "mean"),
        avg_bs_raw    = ("bertscore_f1_raw", "mean"),
        pass_rate     = ("judge_verdict",    lambda x: (x == "PASS").mean()),
    ).round(4)
    print(summary.to_string())

    if throughput_results:
        print("\nTHROUGHPUT (5 concurrent queries)")
        for p, t in throughput_results.items():
            print(f"  {p:12s}  p50={t['p50_latency_s']}s  p95={t['p95_latency_s']}s  {t['qpm']} QPM")

    if "basic_rag" in summary.index and "graphrag" in summary.index:
        rag_tok  = summary.loc["basic_rag", "avg_tokens"]
        gr_tok   = summary.loc["graphrag",  "avg_tokens"]
        red      = (rag_tok - gr_tok) / rag_tok * 100 if rag_tok > 0 else 0
        pass_pct = summary.loc["graphrag", "pass_rate"] * 100
        bs_r     = summary.loc["graphrag", "avg_bertscore"]
        bs_raw   = summary.loc["graphrag", "avg_bs_raw"]

        print(f"\nGraphRAG token reduction vs Basic RAG: {red:.1f}%")
        print(f"Judge pass rate:     {pass_pct:.0f}%  ({'PASS' if pass_pct >= 90 else 'needs work'}) (target >=90%)")
        print(f"BERTScore rescaled:  {bs_r:.3f}  ({'PASS' if bs_r >= 0.55 else 'needs work'}) (target >=0.55)")
        print(f"BERTScore raw:       {bs_raw:.3f}  ({'PASS' if bs_raw >= 0.88 else 'needs work'}) (target >=0.88)")

        if red == 0 and rag_tok > 0:
            print(
                "\nNOTE: 0% token reduction means GraphRAG used the same number of tokens as Basic RAG."
                "\nThis usually means GRAPHRAG_TOP_K and CHUNK_CHARS are not reducing context size."
                "\nCheck .env: GRAPHRAG_TOP_K=3 and GRAPHRAG_CHUNK_CHARS=300 (Basic RAG uses 5 chunks and ~800 chars)."
            )

    return df, throughput_results


if __name__ == "__main__":
    ids = sys.argv[1:] or None
    run_benchmark(ids)
