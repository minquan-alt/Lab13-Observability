from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import List, Optional
from pydantic import BaseModel
from langfuse import get_client

from . import metrics
from .mock_llm import FakeLLM
from .mock_rag import retrieve
from .pii import hash_user_id, summarize_text
from .tracing import langfuse_context, observe


@dataclass
class AgentResult:
    answer: str
    latency_ms: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    quality_score: float
    relevancy_score: float
    faithfulness_score: float


class LabAgent:
    def __init__(self, model: str = "claude-sonnet-4-5") -> None:
        self.model = model
        self.llm = FakeLLM(model=model)

    def run(self, user_id: str, feature: str, session_id: str, message: str) -> AgentResult:
        client = get_client()
        # Start a span manually to ensure it is linked to the trace
        with client.start_as_current_span(
            name="Agent Run",
            input={"message": message},
        ) as root_span:
            # Update trace level attributes
            client.update_current_trace(
                user_id=hash_user_id(user_id),
                session_id=session_id,
                metadata={"feature": feature, "model": self.model}
            )
            started = time.perf_counter()
            docs = retrieve(message)
            
            response = self.llm.generate(
                prompt=f"Context: {docs}\nQuestion: {message}"
            )
            
            latency_ms = (time.perf_counter() - started) * 1000
            cost_usd = (response.usage.input_tokens * 0.01 + response.usage.output_tokens * 0.03) / 1000
            quality_score = self._heuristic_quality(message, response.text, docs)

            root_span.update(
                output={"answer": response.text},
                metadata={"quality_score": quality_score}
            )

            langfuse_context.score(
                name="quality",
                value=quality_score,
                comment="Heuristic quality score",
            )
            langfuse_context.flush()

            metrics.record_request(
                latency_ms=latency_ms,
                cost_usd=cost_usd,
                tokens_in=response.usage.input_tokens,
                tokens_out=response.usage.output_tokens,
                quality_score=quality_score,
            )

            result = AgentResult(
                answer=response.text,
                latency_ms=int(latency_ms),
                tokens_in=response.usage.input_tokens,
                tokens_out=response.usage.output_tokens,
                cost_usd=cost_usd,
                quality_score=quality_score,
                relevancy_score=0.0,
                faithfulness_score=0.0,
            )

        self._persist_trace(user_id, feature, session_id, message, result)
        return result

    def _persist_trace(self, user_id: str, feature: str, session_id: str, message: str, result: AgentResult) -> None:
        os.makedirs("data", exist_ok=True)
        record = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "user_id_hash": hash_user_id(user_id),
            "session_id": session_id,
            "feature": feature,
            "model": self.model,
            "message": message,
            "answer": result.answer,
            "latency_ms": result.latency_ms,
            "tokens_in": result.tokens_in,
            "tokens_out": result.tokens_out,
            "cost_usd": result.cost_usd,
            "quality": result.quality_score,
            "relevancy": result.relevancy_score,
            "faithfulness": result.faithfulness_score,
        }
        with open("data/trace_history.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def _estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        input_cost = (tokens_in / 1_000_000) * 3
        output_cost = (tokens_out / 1_000_000) * 15
        return round(input_cost + output_cost, 6)

    def _heuristic_quality(self, question: str, answer: str, docs: list[str]) -> float:
        score = 0.5
        if docs:
            score += 0.2
        if len(answer) > 40:
            score += 0.1
        if question.lower().split()[0:1] and any(token in answer.lower() for token in question.lower().split()[:3]):
            score += 0.1
        if "[REDACTED" in answer:
            score -= 0.2
        return round(max(0.0, min(1.0, score)), 2)
