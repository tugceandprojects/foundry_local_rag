from __future__ import annotations

import pytest

from local_rag.database import KnowledgeDatabase


def _fake_vector(text: str, dims: int = 16) -> list[float]:
    """Karakter frekansına dayalı, deterministik ve gerçek bir embedding
    modeli olmadan da anlamlı "benzer metinler -> benzer vektör" davranışı
    gösteren basit bir sahte vektör üretir.
    """
    vector = [0.0] * dims
    for char in text.lower():
        vector[ord(char) % dims] += 1.0
    norm = sum(v * v for v in vector) ** 0.5
    if norm == 0.0:
        return vector
    return [v / norm for v in vector]


class FakeRuntime:
    """`ModelRuntime` arayüzünü uygulayan, model indirmeden çalışan sahte
    sağlayıcı. Foundry SDK'sını sahte nesnelerle değiştirebildiğimiz için
    tüm iş mantığını model indirmeden test edebiliriz (bkz. PROJE_REHBERI.md).
    """

    def __init__(self):
        self.chat_calls: list[tuple[str, str]] = []
        self.next_chat_response: str | None = None

    def embed(self, texts):
        return [_fake_vector(text) for text in texts]

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        self.chat_calls.append((system_prompt, user_prompt))
        if self.next_chat_response is not None:
            return self.next_chat_response
        return f"[sahte cevap] {user_prompt}"


@pytest.fixture
def fake_runtime() -> FakeRuntime:
    return FakeRuntime()


@pytest.fixture
def database(tmp_path) -> KnowledgeDatabase:
    db = KnowledgeDatabase(tmp_path / "test.db")
    db.initialize()
    return db
