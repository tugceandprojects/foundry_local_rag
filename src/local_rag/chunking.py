"""Belge metnini örtüşmeli (overlap) karakter tabanlı parçalara ayırır."""

from __future__ import annotations

import re


def normalize_whitespace(text: str) -> str:
    """Ardışık boşluk/satır sonlarını tek boşluğa indirger."""
    return re.sub(r"\s+", " ", text).strip()


def chunk_text(text: str, chunk_size: int = 800, chunk_overlap: int = 120) -> list[str]:
    """Metni `chunk_size` karakterlik, `chunk_overlap` kadar örtüşen parçalara böler.

    Örtüşme (overlap), bir cümlenin tam olarak iki parça sınırına denk gelip
    anlamının kaybolmasını engeller. Boş metin için boş liste döner.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size pozitif olmalıdır")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap negatif olamaz")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap, chunk_size'dan küçük olmalıdır")

    normalized = normalize_whitespace(text)
    if not normalized:
        return []

    step = chunk_size - chunk_overlap
    chunks: list[str] = []
    start = 0
    length = len(normalized)
    while start < length:
        end = min(start + chunk_size, length)
        piece = normalized[start:end].strip()
        if piece:
            chunks.append(piece)
        if end == length:
            break
        start += step
    return chunks
