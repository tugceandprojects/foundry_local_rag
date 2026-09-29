"""Retrieval ve generation adımlarını birleştiren RAG orkestrasyonu.

Prompt kuralları ve "yetersiz bilgide cevap vermeyi reddetme" davranışı
burada tanımlıdır (bkz. PROJE_REHBERI.md, "Kodun katmanları").
"""

from __future__ import annotations

from dataclasses import dataclass

from .providers import ModelRuntime
from .retrieval import RetrievedChunk, Retriever

NO_CONTEXT_MESSAGE = "Bu bilgi belgelerde bulunamadı."

SYSTEM_PROMPT = (
    "Sen yalnızca sana verilen bağlamdaki bilgilere dayanarak Türkçe cevap "
    "veren bir yerel belge asistanısın. Bağlamda yer almayan hiçbir bilgiyi "
    "uydurma. Sorunun cevabı bağlamda yoksa, açıkça 'Bu bilgi belgelerde "
    "bulunamadı.' de. Mümkün olduğunda cevabında hangi kaynaktan "
    "yararlandığını belirt.\n\nBağlam:\n{context}"
)


def _locate(chunk: RetrievedChunk) -> str:
    """PDF bölümleri için 'sayfa N', diğer belgeler için 'bölüm N' üretir."""
    if chunk.page is not None:
        return f"sayfa {chunk.page}"
    return f"bölüm {chunk.position + 1}"


@dataclass(frozen=True)
class Answer:
    """Kullanıcıya döndürülen nihai cevap ve dayandığı kaynak bölümler."""

    text: str
    sources: list[RetrievedChunk]


class RagService:
    """Retrieval + generation akışını yürütür; güven eşiğinin altındaki
    sonuçlarda dil modelini hiç çağırmayarak uydurma (hallucination)
    riskini ve gereksiz hesaplamayı azaltır.
    """

    def __init__(self, retriever: Retriever, runtime: ModelRuntime, top_k: int, min_score: float):
        self._retriever = retriever
        self._runtime = runtime
        self._top_k = top_k
        self._min_score = min_score

    def answer(self, question: str) -> Answer:
        question = question.strip()
        if not question:
            return Answer(text="Lütfen bir soru yazın.", sources=[])

        candidates = self._retriever.retrieve(question, self._top_k)
        relevant = [chunk for chunk in candidates if chunk.score >= self._min_score]
        if not relevant:
            return Answer(text=NO_CONTEXT_MESSAGE, sources=[])

        context = "\n\n".join(
            f"[Kaynak: {chunk.source} - {_locate(chunk)}]\n{chunk.content}" for chunk in relevant
        )
        system_prompt = SYSTEM_PROMPT.format(context=context)
        text = self._runtime.chat(system_prompt, question).strip()
        return Answer(text=text or NO_CONTEXT_MESSAGE, sources=relevant)
