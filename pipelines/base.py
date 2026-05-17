"""
Shared base class for all pipelines.
Every pipeline returns a PipelineResult with tokens, latency, cost, answer.
"""

import time, os
from dataclasses import dataclass
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ── pricing per 1M tokens ─────────────────────────────────────────────────────
_PROVIDER_PRICING = {
    "gemini-1.5-flash": (0.075, 0.30),
    "gemini-1.5-pro":   (3.50,  10.50),
    "gemini-2.0-flash": (0.10,  0.40),
    "gpt-4o-mini":      (0.15,  0.60),
    "gpt-4o":           (5.00,  15.00),
}

def get_pricing(model: str) -> tuple:
    for key, price in _PROVIDER_PRICING.items():
        if key in model:
            return price
    return (0.15, 0.60)


def count_tokens(text: str, model: str = None) -> int:
    try:
        import tiktoken
        model = model or os.environ.get("LLM_MODEL", "gpt-4o-mini")
        try:
            enc = tiktoken.encoding_for_model(model)
        except KeyError:
            enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except ImportError:
        return int(len(text.split()) * 1.33)


def get_llm_client() -> OpenAI:
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        return OpenAI(
            api_key=gemini_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
    return OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    )


def llm_call(client: OpenAI, system: str, user: str, model: str = None) -> tuple:
    """Returns (answer, prompt_tokens, completion_tokens)."""
    model = model or os.environ.get("LLM_MODEL", "gemini-1.5-flash")
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=0,
    )
    return resp.choices[0].message.content, resp.usage.prompt_tokens, resp.usage.completion_tokens


def calc_cost(prompt_tokens: int, completion_tokens: int, model: str = None) -> float:
    model = model or os.environ.get("LLM_MODEL", "gemini-1.5-flash")
    price_in, price_out = get_pricing(model)
    return round((prompt_tokens * price_in + completion_tokens * price_out) / 1_000_000, 6)


@dataclass
class PipelineResult:
    pipeline:          str
    answer:            str
    prompt_tokens:     int
    completion_tokens: int
    latency_s:         float
    context_used:      str  = ""
    error:             str  = ""
    entities:          dict = None
    traversal_hops:    list = None

    @property
    def total_tokens(self):
        return self.prompt_tokens + self.completion_tokens

    @property
    def cost_usd(self):
        model = os.environ.get("LLM_MODEL", "gemini-1.5-flash")
        price_in, price_out = get_pricing(model)
        return round(
            (self.prompt_tokens * price_in + self.completion_tokens * price_out) / 1_000_000, 6
        )

    def as_dict(self):
        return {
            "pipeline":          self.pipeline,
            "answer":            self.answer,
            "prompt_tokens":     self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens":      self.total_tokens,
            "latency_s":         round(self.latency_s, 3),
            "cost_usd":          self.cost_usd,
            "error":             self.error,
        }


class BasePipeline:
    name = "base"

    def __init__(self):
        self.client = get_llm_client()

    def run(self, query: str) -> PipelineResult:
        raise NotImplementedError

    def _timed_run(self, query: str) -> PipelineResult:
        t0 = time.perf_counter()
        try:
            result = self.run(query)
        except Exception as e:
            result = PipelineResult(
                pipeline=self.name, answer="", prompt_tokens=0,
                completion_tokens=0, latency_s=round(time.perf_counter() - t0, 3), error=str(e),
            )
        result.latency_s = round(time.perf_counter() - t0, 3)
        return result
