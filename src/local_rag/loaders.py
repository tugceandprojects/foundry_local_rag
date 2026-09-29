"""Desteklenen dosya türlerinden (.txt, .md, .pdf) metin çıkarır.

PDF'ler sayfa sayfa okunur; bu sayede ingestion aşamasında her bölümün
hangi sayfadan geldiği izlenebilir ve kaynak gösterirken "sayfa 7" gibi
öğrenci için anlamlı bir referans verilebilir. `.txt`/`.md` dosyalarında
sayfa kavramı olmadığı için tek bir "sayfa" olarak ele alınır.
"""

from __future__ import annotations

from pathlib import Path

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}


def extract_pages(path: Path) -> list[str]:
    """Dosyayı sayfa/bölüm metinlerinden oluşan bir listeye çevirir.

    `.txt` ve `.md` dosyaları tek elemanlı bir liste döner (tüm içerik).
    `.pdf` dosyaları her sayfa için bir eleman döner (boş sayfalar dahil,
    sıralama korunur ki sayfa numaraları doğru kalsın).
    """
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return [path.read_text(encoding="utf-8")]
    if suffix == ".pdf":
        return _extract_pdf_pages(path)
    raise ValueError(f"Desteklenmeyen dosya türü: {suffix}")


def _extract_pdf_pages(path: Path) -> list[str]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - sadece pypdf kurulu değilse
        raise RuntimeError(
            "PDF okumak için 'pypdf' gerekir. 'pip install pypdf' ile kurun."
        ) from exc

    reader = PdfReader(str(path))
    return [page.extract_text() or "" for page in reader.pages]
