"""Deterministik arama katmanı: sorguyu embed eder, kosinüs benzerliğine göre
en ilgili belge bölümlerini bulur.

Yapay zekâ üretiminden (chat) farklı olarak bu katman rastgelelik içermez:
aynı vektörler için her zaman aynı sıralamayı verir.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .database import KnowledgeDatabase
from .providers import ModelRuntime


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """İki vektör arasındaki kosinüs benzerliğini hesaplar (-1..1 aralığında)."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


@dataclass(frozen=True)
class RetrievedChunk:
    """Bir sorguyla eşleşen, benzerlik puanı eklenmiş belge bölümü."""

    source: str
    position: int
    content: str
    score: float
    page: int | None = None


class Retriever:
    """Veritabanındaki tüm bölümleri sorgu vektörüyle brute-force karşılaştırır.

    Küçük veri kümeleri için bu yaklaşım yeterlidir; veri büyüdükçe özel bir
    vektör indeksi (örn. FAISS, sqlite-vec) gerekir (bkz. README sınırlamalar).
    """

    def __init__(self, database: KnowledgeDatabase, runtime: ModelRuntime):
        self._database = database
        self._runtime = runtime

    def retrieve(self, query: str, top_k: int) -> list[RetrievedChunk]:
        chunks = self._database.all_chunks()
        if not chunks:
            return []
        query_embedding = self._runtime.embed([query])[0]
        scored = [
            RetrievedChunk(
                source=chunk.source,
                position=chunk.position,
                content=chunk.content,
                score=cosine_similarity(query_embedding, chunk.embedding),
                page=chunk.page,
            )
            for chunk in chunks
        ]
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[: max(top_k, 0)]
