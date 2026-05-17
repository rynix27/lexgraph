"""
Ingest SC judgment cases into ChromaDB (required) and TigerGraph (optional).

Usage:
    python data/ingest.py           # ChromaDB only (safe default)
    python data/ingest.py chroma    # ChromaDB only
    python data/ingest.py tg        # TigerGraph only
    python data/ingest.py both      # Both (TigerGraph must be configured)

ChromaDB is required for all 3 pipelines to work.
TigerGraph enables the full multi-hop GraphRAG path (optional — fallback preserves token reduction).
"""

import os, json, re, sys
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

RAW_PATH   = Path(__file__).parent / "raw" / "ildc_cases.jsonl"
CHROMA_DIR = Path(__file__).parent / "chroma_db"

CHUNK_SIZE    = 512
CHUNK_OVERLAP = 64
MAX_CASES     = 5000


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        chunks.append(" ".join(words[i: i + size]))
        i += size - overlap
    return chunks


def extract_metadata(text: str, case: dict) -> dict:
    year_match = re.search(r"\b(19[5-9]\d|20[0-2]\d)\b", text[:500])
    year       = int(year_match.group()) if year_match else None
    articles   = case.get("articles") or list(set(re.findall(r"Article\s+(\d+[A-Z]?)", text)))[:10]
    judges     = case.get("judges", [])
    acts       = list(set(re.findall(r"([A-Z][a-z]+(?: [A-Z][a-z]+)* Act,?\s*\d{4})", text)))[:5]
    acts       = [a[0] if isinstance(a, tuple) else a for a in acts]
    return {"year": year, "articles": articles, "acts": acts, "judges": judges}


def load_cases(limit: int = MAX_CASES) -> list:
    if not RAW_PATH.exists():
        print(f"Raw data not found at {RAW_PATH}")
        print("Fix: python generate_data.py")
        sys.exit(1)

    cases = []
    with open(RAW_PATH, encoding="utf-8") as f:
        for line in f:
            if len(cases) >= limit:
                break
            row = json.loads(line.strip())
            if not row.get("text") or len(row["text"]) < 100:
                continue
            meta = extract_metadata(row["text"], row)
            cases.append({**row, "meta": meta})

    print(f"Loaded {len(cases):,} cases from {RAW_PATH}")
    return cases


# ── ChromaDB ──────────────────────────────────────────────────────────────────

def ingest_chromadb(cases: list):
    import chromadb
    from sentence_transformers import SentenceTransformer

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    print("Loading embedding model (all-MiniLM-L6-v2)...")
    embedder   = SentenceTransformer("all-MiniLM-L6-v2")
    client     = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Drop and recreate to ensure clean state
    try:
        client.delete_collection("lexgraph_cases")
        print("Dropped existing collection for fresh ingest.")
    except Exception:
        pass

    collection = client.create_collection("lexgraph_cases")

    ids_batch, emb_batch, doc_batch, meta_batch = [], [], [], []
    FLUSH_SIZE = 512

    def flush():
        if ids_batch:
            collection.upsert(
                ids=ids_batch[:], embeddings=emb_batch[:],
                documents=doc_batch[:], metadatas=meta_batch[:],
            )
            ids_batch.clear(); emb_batch.clear()
            doc_batch.clear(); meta_batch.clear()

    print(f"Chunking + embedding {len(cases):,} cases into ChromaDB...")
    for case in tqdm(cases):
        chunks = chunk_text(case["text"])
        for idx, chunk in enumerate(chunks[:8]):
            chunk_id  = f"{case['case_id']}_chunk_{idx}"
            embedding = embedder.encode(chunk).tolist()
            ids_batch.append(chunk_id)
            emb_batch.append(embedding)
            doc_batch.append(chunk)
            meta_batch.append({
                "case_id": case["case_id"],
                "title":   case["title"],
                "year":    str(case["meta"].get("year") or ""),
                "chunk":   idx,
            })
            if len(ids_batch) >= FLUSH_SIZE:
                flush()

    flush()
    print(f"ChromaDB done. {collection.count():,} chunks stored at {CHROMA_DIR}")


# ── TigerGraph ────────────────────────────────────────────────────────────────

def get_tg_connection():
    import pyTigerGraph as tg

    tg_host   = os.environ.get("TG_HOST", "")
    tg_user   = os.environ.get("TG_USERNAME", "tigergraph")
    tg_pass   = os.environ.get("TG_PASSWORD", "")
    tg_secret = os.environ.get("TG_SECRET", "")
    tg_graph  = os.environ.get("TG_GRAPH_NAME", "LexGraph")

    if not tg_host or "your-instance" in tg_host:
        raise RuntimeError("TG_HOST not configured in .env")

    conn = tg.TigerGraphConnection(
        host=tg_host,
        username=tg_user,
        password=tg_pass,
        gsqlSecret=tg_secret if tg_secret and not tg_pass else "",
        graphname=tg_graph,
    )
    if tg_secret:
        conn.getToken(tg_secret)
    else:
        conn.getToken(conn.createSecret())
    return conn


def setup_tigergraph_schema(conn):
    print("Setting up TigerGraph schema...")
    try:
        conn.gsql("""
            CREATE VERTEX IF NOT EXISTS Case (
                PRIMARY_ID case_id STRING,
                title      STRING DEFAULT "",
                year       INT    DEFAULT 0,
                text_chunk STRING DEFAULT ""
            ) WITH primary_id_as_attribute="true"

            CREATE VERTEX IF NOT EXISTS Article (
                PRIMARY_ID article_id STRING,
                number     STRING DEFAULT ""
            ) WITH primary_id_as_attribute="true"

            CREATE VERTEX IF NOT EXISTS Judge (
                PRIMARY_ID judge_id STRING,
                name       STRING DEFAULT ""
            ) WITH primary_id_as_attribute="true"

            CREATE VERTEX IF NOT EXISTS Act (
                PRIMARY_ID act_id STRING,
                name       STRING DEFAULT ""
            ) WITH primary_id_as_attribute="true"

            CREATE DIRECTED EDGE references_article (FROM Case, TO Article)
            CREATE DIRECTED EDGE authored_by       (FROM Case, TO Judge)
            CREATE DIRECTED EDGE references_act    (FROM Case, TO Act)
            CREATE UNDIRECTED EDGE cites           (FROM Case, TO Case)
        """)
        print("Schema created.")
    except Exception as e:
        print(f"Schema note (may already exist): {e}")


def ingest_tigergraph(cases: list):
    try:
        conn = get_tg_connection()
    except RuntimeError as e:
        print(f"TigerGraph skipped: {e}")
        return

    setup_tigergraph_schema(conn)
    print(f"Ingesting {len(cases):,} cases into TigerGraph...")

    for i in tqdm(range(0, len(cases), 50)):
        batch = cases[i: i + 50]
        for c in batch:
            try:
                conn.upsertVertex("Case", c["case_id"], {
                    "title":      c["title"][:200],
                    "year":       c["meta"].get("year") or 0,
                    "text_chunk": c["text"][:2000],
                })
                for art_num in c["meta"].get("articles", []):
                    art_id = f"Art_{art_num}"
                    conn.upsertVertex("Article", art_id, {"number": art_num})
                    conn.upsertEdge("Case", c["case_id"], "references_article", "Article", art_id)
                for judge in c["meta"].get("judges", []):
                    judge_id = re.sub(r"\W+", "_", judge)
                    conn.upsertVertex("Judge", judge_id, {"name": judge})
                    conn.upsertEdge("Case", c["case_id"], "authored_by", "Judge", judge_id)
                for act in c["meta"].get("acts", []):
                    act_id = re.sub(r"\W+", "_", act)
                    conn.upsertVertex("Act", act_id, {"name": act})
                    conn.upsertEdge("Case", c["case_id"], "references_act", "Act", act_id)
            except Exception as e:
                pass   # skip individual vertex errors silently

    print("TigerGraph ingest complete.")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cases  = load_cases()
    target = sys.argv[1] if len(sys.argv) > 1 else "chroma"

    if target in ("both", "chroma"):
        ingest_chromadb(cases)

    if target in ("both", "tg"):
        ingest_tigergraph(cases)

    print(f"\nDone. Next: python preflight.py")
