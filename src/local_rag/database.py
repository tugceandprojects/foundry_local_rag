"""Belge bölümlerini ve embedding vektörlerini SQLite'ta saklayan katman."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StoredChunk:
    """Veritabanında saklanan bir belge bölümü."""

    id: int
    source: str
    position: int
    content: str
    embedding: list[float]
    page: int | None = None


@dataclass(frozen=True)
class SourceSummary:
    """Bir kaynak dosyanın indeksteki özeti (arayüzdeki dosya listesi için)."""

    source: str
    chunks: int
    pages: int


class KnowledgeDatabase:
    """`chunks` tablosu üzerinden basit CRUD işlemleri sağlar.

    Embedding vektörleri JSON metin olarak saklanır; bu, küçük veri
    kümelerinde kurulumu basit ve veritabanını herhangi bir SQLite
    aracıyla incelenebilir tutar (bkz. README "Tasarım kararları").
    """

    def __init__(self, path: str | Path):
        self._path = Path(path)

    @property
    def path(self) -> Path:
        return self._path

    def initialize(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    embedding TEXT NOT NULL,
                    page INTEGER
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_source ON chunks(source)")

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self._path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def clear_all(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM chunks")

    def clear_source(self, source: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM chunks WHERE source = ?", (source,))

    def add_chunk(
        self,
        source: str,
        position: int,
        content: str,
        embedding: Sequence[float],
        page: int | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO chunks (source, position, content, embedding, page) VALUES (?, ?, ?, ?, ?)",
                (source, position, content, json.dumps(list(embedding)), page),
            )

    def count(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()
        return int(row[0]) if row else 0

    def all_chunks(self) -> list[StoredChunk]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, source, position, content, embedding, page "
                "FROM chunks ORDER BY source, position"
            ).fetchall()
        return [
            StoredChunk(
                id=row[0],
                source=row[1],
                position=row[2],
                content=row[3],
                embedding=json.loads(row[4]),
                page=row[5],
            )
            for row in rows
        ]

    def sources_summary(self) -> list[SourceSummary]:
        """Her kaynak dosya için bölüm ve (PDF ise) sayfa sayısını döner."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT source, COUNT(*), COUNT(DISTINCT page) "
                "FROM chunks GROUP BY source ORDER BY source"
            ).fetchall()
        return [SourceSummary(source=r[0], chunks=r[1], pages=r[2]) for r in rows]
