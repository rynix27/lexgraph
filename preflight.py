"""
preflight.py — run this BEFORE benchmark_1.py to catch every setup issue.

Usage:
    python preflight.py

Checks:
  1. .env loaded with required keys
  2. ChromaDB collection exists and is populated
  3. LLM API key works (small test call)
  4. TigerGraph reachable (optional — warns, does not fail)
  5. All pipeline imports work
"""

import os, sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv()

PASS  = "PASS"
FAIL  = "FAIL"
WARN  = "WARN"
SKIP  = "SKIP"

results = []

def check(name, fn):
    try:
        status, msg = fn()
    except Exception as e:
        status, msg = FAIL, str(e)
    tag = f"[{status}]"
    print(f"  {tag:6s}  {name}")
    if msg:
        print(f"         {msg}")
    results.append((name, status, msg))
    return status


# ── 1. Environment variables ──────────────────────────────────────────────────
def check_env():
    missing = []
    for key in ["GEMINI_API_KEY", "LLM_MODEL"]:
        if not os.environ.get(key):
            missing.append(key)
    if missing:
        return FAIL, f"Missing in .env: {', '.join(missing)}"
    model = os.environ.get("LLM_MODEL","")
    key   = os.environ.get("GEMINI_API_KEY","")
    return PASS, f"LLM_MODEL={model}  key={'set' if key else 'MISSING'}"


# ── 2. ChromaDB collection ────────────────────────────────────────────────────
def check_chromadb():
    chroma_dir = Path("data/chroma_db")
    if not chroma_dir.exists():
        return FAIL, (
            "data/chroma_db not found.\n"
            "         Fix: python generate_data.py && python data/ingest.py"
        )
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(chroma_dir))
        col = client.get_collection("lexgraph_cases")
        count = col.count()
        if count == 0:
            return FAIL, (
                "ChromaDB collection 'lexgraph_cases' is empty.\n"
                "         Fix: python generate_data.py && python data/ingest.py"
            )
        return PASS, f"{count:,} chunks indexed in ChromaDB"
    except Exception as e:
        if "does not exist" in str(e) or "not found" in str(e).lower():
            return FAIL, (
                "Collection 'lexgraph_cases' not found.\n"
                "         Fix: python generate_data.py && python data/ingest.py"
            )
        return FAIL, str(e)


# ── 3. LLM API key ────────────────────────────────────────────────────────────
def check_llm():
    from openai import OpenAI
    key   = os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("LLM_MODEL", "gemini-1.5-flash")
    if not key:
        return FAIL, "No GEMINI_API_KEY or OPENAI_API_KEY set in .env"

    base_url = None
    if os.environ.get("GEMINI_API_KEY"):
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"

    client = OpenAI(api_key=key, base_url=base_url) if base_url else OpenAI(api_key=key)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role":"user","content":"Reply with the single word: ready"}],
        temperature=0,
        max_tokens=5,
    )
    reply = resp.choices[0].message.content.strip()
    tokens = resp.usage.prompt_tokens + resp.usage.completion_tokens
    return PASS, f"LLM responded: '{reply}' ({tokens} tokens used)"


# ── 4. TigerGraph (optional) ──────────────────────────────────────────────────
def check_tigergraph():
    host = os.environ.get("TG_HOST","")
    if not host or "your-instance" in host:
        return SKIP, "TG_HOST not configured — GraphRAG will use ChromaDB fallback"
    try:
        import pyTigerGraph as tg
        conn = tg.TigerGraphConnection(
            host=os.environ["TG_HOST"],
            username=os.environ.get("TG_USERNAME","tigergraph"),
            password=os.environ.get("TG_PASSWORD",""),
            gsqlSecret=os.environ.get("TG_SECRET",""),
            graphname=os.environ.get("TG_GRAPH_NAME","LexGraph"),
        )
        conn.getToken(os.environ.get("TG_SECRET",""))
        info = conn.getGraphInfo()
        return PASS, f"Connected to TigerGraph: {host}"
    except Exception as e:
        return WARN, (
            f"TigerGraph unreachable: {str(e)[:120]}\n"
            "         GraphRAG will use graph-enhanced ChromaDB fallback (token reduction preserved)"
        )


# ── 5. Pipeline imports ───────────────────────────────────────────────────────
def check_pipelines():
    from pipelines import LLMOnlyPipeline, BasicRAGPipeline, GraphRAGPipeline
    return PASS, "All 3 pipeline classes import successfully"


# ── 6. Raw data file ──────────────────────────────────────────────────────────
def check_raw_data():
    raw = Path("data/raw/ildc_cases.jsonl")
    if not raw.exists():
        return FAIL, (
            "data/raw/ildc_cases.jsonl not found.\n"
            "         Fix: python generate_data.py"
        )
    with open(raw) as f:
        count = sum(1 for _ in f)
    size_mb = raw.stat().st_size / 1_000_000
    return PASS, f"{count:,} cases  ({size_mb:.1f} MB)"


# ── Run all checks ────────────────────────────────────────────────────────────
print("\nLexGraph pre-flight checks")
print("=" * 50)

check("Environment variables (.env)",    check_env)
check("Raw data file",                   check_raw_data)
check("ChromaDB collection",             check_chromadb)
check("LLM API key (live test)",         check_llm)
check("TigerGraph connection",           check_tigergraph)
check("Pipeline imports",                check_pipelines)

print("=" * 50)
failures = [r for r in results if r[1] == FAIL]
warnings = [r for r in results if r[1] == WARN]

if failures:
    print(f"\n{len(failures)} check(s) FAILED — fix these before running benchmark_1.py\n")
    for name, _, msg in failures:
        print(f"  - {name}")
    sys.exit(1)
elif warnings:
    print(f"\nAll checks passed ({len(warnings)} warning(s)) — ready to run benchmark_1.py")
    print("Note: TigerGraph warnings are non-fatal. GraphRAG fallback maintains token reduction.")
else:
    print("\nAll checks passed — run: python eval/benchmark_1.py")
