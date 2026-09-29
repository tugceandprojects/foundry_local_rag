from __future__ import annotations

import pytest

from local_rag.chunking import chunk_text, normalize_whitespace


def test_normalize_whitespace_collapses_and_trims():
    assert normalize_whitespace("  Merhaba   dünya\n\n") == "Merhaba dünya"


def test_chunk_text_empty_input_returns_empty_list():
    assert chunk_text("", chunk_size=10, chunk_overlap=2) == []
    assert chunk_text("   ", chunk_size=10, chunk_overlap=2) == []


def test_chunk_text_short_text_returns_single_chunk():
    text = "Kısa bir metin."
    chunks = chunk_text(text, chunk_size=100, chunk_overlap=10)
    assert chunks == [text]


def test_chunk_text_splits_long_text_into_multiple_chunks():
    text = "a" * 250
    chunks = chunk_text(text, chunk_size=100, chunk_overlap=20)
    assert len(chunks) > 1
    assert all(len(chunk) <= 100 for chunk in chunks)


def test_chunk_text_consecutive_chunks_overlap():
    text = "0123456789" * 5  # 50 karakter
    chunks = chunk_text(text, chunk_size=20, chunk_overlap=5)
    # İkinci parçanın başı, ilk parçanın sonuyla örtüşmeli
    assert chunks[0][-5:] == chunks[1][:5]


@pytest.mark.parametrize(
    "chunk_size,chunk_overlap",
    [(0, 0), (-5, 0), (10, 10), (10, 15)],
)
def test_chunk_text_rejects_invalid_sizes(chunk_size, chunk_overlap):
    with pytest.raises(ValueError):
        chunk_text("herhangi bir metin", chunk_size=chunk_size, chunk_overlap=chunk_overlap)
