"""Belge klasöründeki dosyaları okuyup parçalayan, embedding üreten ve
SQLite'a yazan ingestion (indeksleme) akışı.
"""

from __future__ import annotations

from pathlib import Path

from .chunking import chunk_text
from .database import KnowledgeDatabase
from .loaders import SUPPORTED_EXTENSIONS, extract_pages
from .providers import ModelRuntime

__all__ = ["SUPPORTED_EXTENSIONS", "ingest"]


def ingest(
    documents_path: str | Path,
    database: KnowledgeDatabase,
    runtime: ModelRuntime,
    chunk_size: int,
    chunk_overlap: int,
) -> int:
    """`documents_path` altındaki `.txt`/`.md`/`.pdf` dosyalarını yeniden indeksler.

    Her çağrıda veritabanı önce tamamen temizlenir, böylece silinen veya
    değiştirilen dosyalar eski/artık kalıntı bölüm bırakmaz. PDF'lerde her
    sayfa ayrı ayrı parçalanır ve sayfa numarası saklanır, böylece daha
    sonra "sayfa 7'de şöyle deniyor" gibi kaynak gösterilebilir. Toplam
    indekslenen bölüm sayısını döner.
    """
    documents_path = Path(documents_path)
    database.clear_all()
    if not documents_path.exists():
        return 0

    total_chunks = 0
    for file_path in sorted(documents_path.rglob("*")):
        if not file_path.is_file() or file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        is_paged_source = file_path.suffix.lower() == ".pdf"
        pages = extract_pages(file_path)

        position = 0
        for page_number, page_text in enumerate(pages, start=1):
            chunks = chunk_text(page_text, chunk_size, chunk_overlap)
            if not chunks:
                continue
            embeddings = runtime.embed(chunks)
            page_value = page_number if is_paged_source else None
            for content, embedding in zip(chunks, embeddings):
                database.add_chunk(file_path.name, position, content, embedding, page=page_value)
                position += 1
        total_chunks += position

    return total_chunks
