"""Uygulama ayarlarını .env dosyasından ve ortam değişkenlerinden okur."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv(path: Path | None = None) -> None:
    """`.env` dosyasındaki KEY=VALUE satırlarını ortam değişkenlerine yükler.

    Zaten ortamda tanımlı olan değişkenlerin üzerine yazmaz, böylece komut
    satırından `RAG_TOP_K=5 python -m local_rag.cli chat` gibi geçici
    override'lar her zaman önceliklidir.
    """
    dotenv_path = path or Path(".env")
    if not dotenv_path.exists():
        return
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


@dataclass(frozen=True)
class Settings:
    """Uygulama genelinde kullanılan yapılandırma değerleri."""

    database_path: Path
    documents_path: Path
    embedding_model: str
    chat_model: str
    chunk_size: int
    chunk_overlap: int
    top_k: int
    min_score: float

    @classmethod
    def from_env(cls, dotenv_path: Path | None = None) -> Settings:
        _load_dotenv(dotenv_path)
        return cls(
            database_path=Path(os.environ.get("RAG_DATABASE", "data/knowledge.db")),
            documents_path=Path(os.environ.get("RAG_DOCUMENTS", "documents")),
            embedding_model=os.environ.get("RAG_EMBEDDING_MODEL", "qwen3-embedding-0.6b"),
            chat_model=os.environ.get("RAG_CHAT_MODEL", "qwen2.5-0.5b"),
            chunk_size=int(os.environ.get("RAG_CHUNK_SIZE", "800")),
            chunk_overlap=int(os.environ.get("RAG_CHUNK_OVERLAP", "120")),
            top_k=int(os.environ.get("RAG_TOP_K", "3")),
            min_score=float(os.environ.get("RAG_MIN_SCORE", "0.35")),
        )
