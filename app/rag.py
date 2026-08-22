import hashlib
import math
import os
import re
from dataclasses import dataclass

DIMENSIONS = 128
def embed(text: str) -> list[float]:
    """Deterministic local embedding stub; replace with a provider in production."""
    vector = [0.0] * DIMENSIONS
    for token in re.findall(r"[a-zA-ZÀ-ÿ0-9]+", text.lower()):
        digest = hashlib.sha256(token.encode()).digest()
        vector[int.from_bytes(digest[:2], "big") % DIMENSIONS] += 1 if digest[2] % 2 else -1
    norm = math.sqrt(sum(x*x for x in vector)) or 1
    return [x/norm for x in vector]

def cosine(a: list[float], b: list[float]) -> float: return sum(x*y for x,y in zip(a,b))
def chunks(text: str, size: int = 700, overlap: int = 100) -> list[str]:
    clean = " ".join(text.split()); return [clean[i:i+size] for i in range(0, len(clean), size-overlap) if clean[i:i+size]]

@dataclass
class Generated:
    answer: str; grounded: bool

def generate(question: str, contexts: list[str]) -> Generated:
    if not contexts: return Generated("Non dispongo di informazioni sufficienti nei documenti caricati.", False)
    if os.getenv("LLM_PROVIDER", "stub") == "stub":
        return Generated(f"Risposta basata sui documenti: {contexts[0][:500]}", True)
    # Integration seam: send question + contexts to the configured LLM SDK here.
    raise RuntimeError("Configure an LLM adapter before setting LLM_PROVIDER to a non-stub value")


