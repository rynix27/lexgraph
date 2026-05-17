"""Pipeline 2: Basic RAG — ChromaDB vector search + LLM."""

import os, time
from pathlib import Path
from .base import BasePipeline, PipelineResult, llm_call

CHROMA_DIR = Path(__file__).parent.parent / "data" / "chroma_db"
TOP_K      = 5   # retrieve 5 chunks — GraphRAG uses only 3

SYSTEM = """You are a legal expert on Indian Supreme Court jurisprudence.
Use ONLY the provided case excerpts to answer the question.
Cite the case titles you used. Be precise and concise."""


class BasicRAGPipeline(BasePipeline):
    name = "basic_rag"

    def __init__(self):
        super().__init__()
        self.collection = None
        self.embedder   = None
        self._init_db()

    def _init_db(self):
        """
        Initialize ChromaDB. Raises a clear error if collection is empty —
        tells the user exactly how to fix it instead of silently returning
        empty answers with 0 tokens.
        """
        try:
            import chromadb
            from sentence_transformers import SentenceTransformer

            if not CHROMA_DIR.exists():
                raise RuntimeError(
                    f"ChromaDB not found at {CHROMA_DIR}. "
                    "Run: python generate_data.py && python data/ingest.py"
                )

            client = chromadb.PersistentClient(path=str(CHROMA_DIR))

            try:
                self.collection = client.get_collection("lexgraph_cases")
            except Exception:
                raise RuntimeError(
                    "ChromaDB collection 'lexgraph_cases' not found. "
                    "Run: python generate_data.py && python data/ingest.py"
                )

            count = self.collection.count()
            if count == 0:
                raise RuntimeError(
                    "ChromaDB collection is empty (0 documents). "
                    "Run: python generate_data.py && python data/ingest.py"
                )

            self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"BasicRAG init failed: {e}") from e

    def run(self, query: str) -> PipelineResult:
        t0 = time.perf_counter()

        if self.collection is None or self.embedder is None:
            return PipelineResult(
                pipeline=self.name, answer="",
                prompt_tokens=0, completion_tokens=0,
                latency_s=round(time.perf_counter() - t0, 3),
                error="ChromaDB not initialised — run python data/ingest.py first",
            )

        # 1. Embed query + retrieve top-K full chunks
        q_emb   = self.embedder.encode(query).tolist()
        results = self.collection.query(
            query_embeddings=[q_emb],
            n_results=TOP_K,
            include=["documents", "metadatas"],
        )
        docs  = results["documents"][0]
        metas = results["metadatas"][0]

        # 2. Build full context block (raw chunks, no compression — deliberate)
        #    This is what makes Basic RAG use more tokens than GraphRAG.
        context_parts = []
        for doc, meta in zip(docs, metas):
            context_parts.append(
                f"[{meta.get('title','Unknown')} ({meta.get('year','')})]\n{doc}"
            )
        context = "\n\n---\n\n".join(context_parts)

        # 3. LLM synthesis
        user_prompt = f"CONTEXT:\n{context}\n\nQUESTION: {query}"
        answer, p_tok, c_tok = llm_call(self.client, SYSTEM, user_prompt)

        return PipelineResult(
            pipeline=self.name,
            answer=answer,
            prompt_tokens=p_tok,
            completion_tokens=c_tok,
            latency_s=round(time.perf_counter() - t0, 3),
            context_used=context[:800] + "..." if len(context) > 800 else context,
        )
