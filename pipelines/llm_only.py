"""Pipeline 1: LLM-Only baseline. Raw prompt, no retrieval."""

import time
from .base import BasePipeline, PipelineResult, llm_call

SYSTEM = """You are a legal expert on Indian Supreme Court jurisprudence.
Answer the question using your training knowledge only.
Be concise and cite specific cases where possible."""


class LLMOnlyPipeline(BasePipeline):
    name = "llm_only"

    def run(self, query: str) -> PipelineResult:
        t0 = time.perf_counter()
        answer, p_tok, c_tok = llm_call(self.client, SYSTEM, query)
        return PipelineResult(
            pipeline=self.name,
            answer=answer,
            prompt_tokens=p_tok,
            completion_tokens=c_tok,
            latency_s=round(time.perf_counter() - t0, 3),
            context_used="(none — no retrieval)",
        )
