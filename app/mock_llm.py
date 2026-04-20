from __future__ import annotations

import random
import time
from dataclasses import dataclass

from .incidents import STATE
from .tracing import observe



@dataclass
class FakeUsage:
    input_tokens: int
    output_tokens: int

@dataclass
class FakeResponse:
    text: str
    usage: FakeUsage
    model: str


class FakeLLM:
    def __init__(self, model: str = "claude-sonnet-4-5") -> None:
        self.model = model

    @observe(as_type="generation", name="LLM Generation")
    def generate(self, prompt: str) -> FakeResponse:
        import ast
        

        time.sleep(0.15)
        input_tokens = max(20, len(prompt) // 4)
        output_tokens = random.randint(80, 180)
        if STATE["cost_spike"]:
            output_tokens *= 4
            
        docs = []
        for line in prompt.split('\n'):
            if line.startswith("Docs="):
                try:
                    docs_str = line[len("Docs="):]
                    docs = ast.literal_eval(docs_str)
                except Exception:
                    pass
                break
                
        if not docs or "No domain document matched" in docs[0]:
            answer = "I'm sorry, I couldn't find any relevant cooking guide for your request."
        else:
            doc_context = " ".join(docs)
            answer = f"Here is the culinary advice you requested: {doc_context}"

        return FakeResponse(text=answer, usage=FakeUsage(input_tokens, output_tokens), model=self.model)
