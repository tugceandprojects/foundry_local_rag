from __future__ import annotations

import pytest

from local_rag.loaders import extract_pages


def _make_pdf(path, pages_text: list[str]) -> None:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_font("Helvetica", size=12)
    for text in pages_text:
        pdf.add_page()
        pdf.multi_cell(0, 10, text)
    pdf.output(str(path))


def test_extract_pages_txt_returns_single_item(tmp_path):
    file_path = tmp_path / "not.txt"
    file_path.write_text("merhaba dünya", encoding="utf-8")
    assert extract_pages(file_path) == ["merhaba dünya"]


def test_extract_pages_md_returns_single_item(tmp_path):
    file_path = tmp_path / "not.md"
    file_path.write_text("# Başlık\n\nİçerik", encoding="utf-8")
    assert extract_pages(file_path) == ["# Başlık\n\nİçerik"]


def test_extract_pages_pdf_returns_one_item_per_page(tmp_path):
    file_path = tmp_path / "ders.pdf"
    _make_pdf(file_path, ["Birinci sayfa icerigi", "Ikinci sayfa icerigi"])

    pages = extract_pages(file_path)

    assert len(pages) == 2
    assert "Birinci sayfa" in pages[0]
    assert "Ikinci sayfa" in pages[1]


def test_extract_pages_unsupported_extension_raises(tmp_path):
    file_path = tmp_path / "resim.png"
    file_path.write_bytes(b"\x89PNG")
    with pytest.raises(ValueError):
        extract_pages(file_path)
