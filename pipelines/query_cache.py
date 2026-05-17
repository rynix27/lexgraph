"""
Simple in-memory + disk query cache for pipeline results.

Avoids re-running expensive LLM calls when the same query is submitted twice
in the same session (dashboard warm queries, benchmark re-runs).

Usage:
    cache = QueryCache()
    result = cache.get(pipeline_name, query)
    if result is None:
        result = pipeline.run(query)
        cache.set(pipeline_name, query, result)
"""

import hashlib, json, time
from pathlib import Path
from dataclasses import asdict
from .base import PipelineResult

CACHE_DIR = Path(__file__).parent.parent / ".cache"
CACHE_TTL  = 3600  # 1 hour


class QueryCache:
    def __init__(self, ttl: int = CACHE_TTL):
        self.ttl = ttl
        self._mem: dict[str, tuple[float, PipelineResult]] = {}
        CACHE_DIR.mkdir(exist_ok=True)

    def _key(self, pipeline: str, query: str) -> str:
        h = hashlib.md5(f"{pipeline}:{query.strip().lower()}".encode()).hexdigest()
        return h

    def get(self, pipeline: str, query: str) -> PipelineResult | None:
        k = self._key(pipeline, query)
        # memory first
        if k in self._mem:
            ts, result = self._mem[k]
            if time.time() - ts < self.ttl:
                return result
        # disk
        path = CACHE_DIR / f"{k}.json"
        if path.exists():
            try:
                data = json.loads(path.read_text())
                if time.time() - data["_ts"] < self.ttl:
                    data.pop("_ts")
                    result = PipelineResult(**data)
                    self._mem[k] = (time.time(), result)
                    return result
            except Exception:
                pass
        return None

    def set(self, pipeline: str, query: str, result: PipelineResult):
        k = self._key(pipeline, query)
        self._mem[k] = (time.time(), result)
        try:
            d = result.as_dict()
            d["context_used"]   = result.context_used
            d["error"]          = result.error
            d["entities"]       = result.entities
            d["traversal_hops"] = result.traversal_hops
            d["_ts"]            = time.time()
            (CACHE_DIR / f"{k}.json").write_text(json.dumps(d, default=str))
        except Exception:
            pass

    def clear(self):
        self._mem.clear()
        for f in CACHE_DIR.glob("*.json"):
            f.unlink(missing_ok=True)
