from __future__ import annotations

from local_rag.ingestion import ingest


def _make_pdf(path, pages_text: list[str]) -> None:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_font("Helvetica", size=12)
    for text in pages_text:
        pdf.add_page()
        pdf.multi_cell(0, 10, text)
    pdf.output(str(path))


def test_ingest_empty_directory_returns_zero(tmp_path, database, fake_runtime):
    docs_dir = tmp_path / "documents"
    docs_dir.mkdir()
    count = ingest(docs_dir, database, fake_runtime, chunk_size=200, chunk_overlap=20)
    assert count == 0
    assert database.count() == 0


def test_ingest_missing_directory_returns_zero(tmp_path, database, fake_runtime):
    missing_dir = tmp_path / "yok"
    count = ingest(missing_dir, database, fake_runtime, chunk_size=200, chunk_overlap=20)
    assert count == 0


def test_ingest_reads_txt_and_md_files(tmp_path, database, fake_runtime):
    docs_dir = tmp_path / "documents"
    docs_dir.mkdir()
    (docs_dir / "a.md").write_text("Bu bir Markdown belgesidir. " * 10, encoding="utf-8")
    (docs_dir / "b.txt").write_text("Bu bir düz metin belgesidir. " * 10, encoding="utf-8")
    (docs_dir / "c.docx").write_text("desteklenmeyen tür", encoding="utf-8")

    count = ingest(docs_dir, database, fake_runtime, chunk_size=100, chunk_overlap=10)

    assert count > 0
    assert database.count() == count
    sources = {chunk.source for chunk in database.all_chunks()}
    assert sources == {"a.md", "b.txt"}  # .docx yok sayılmalı


def test_ingest_clears_previous_index_before_reindexing(tmp_path, database, fake_runtime):
    docs_dir = tmp_path / "documents"
    docs_dir.mkdir()
    (docs_dir / "a.md").write_text("ilk içerik", encoding="utf-8")
    ingest(docs_dir, database, fake_runtime, chunk_size=100, chunk_overlap=10)
    first_count = database.count()

    (docs_dir / "a.md").unlink()
    (docs_dir / "b.md").write_text("yeni içerik", encoding="utf-8")
    ingest(docs_dir, database, fake_runtime, chunk_size=100, chunk_overlap=10)

    sources = {chunk.source for chunk in database.all_chunks()}
    assert sources == {"b.md"}
    assert first_count > 0


def test_ingest_reads_pdf_files(tmp_path, database, fake_runtime):
    docs_dir = tmp_path / "documents"
    docs_dir.mkdir()
    _make_pdf(
        docs_dir / "ders1.pdf",
        ["Bu birinci sayfanin icerigidir. " * 5, "Bu ikinci sayfanin icerigidir. " * 5],
    )

    count = ingest(docs_dir, database, fake_runtime, chunk_size=200, chunk_overlap=20)

    assert count > 0
    chunks = database.all_chunks()
    assert all(chunk.source == "ders1.pdf" for chunk in chunks)
    pages = {chunk.page for chunk in chunks}
    assert pages == {1, 2}


def test_ingest_txt_and_md_chunks_have_no_page_number(tmp_path, database, fake_runtime):
    docs_dir = tmp_path / "documents"
    docs_dir.mkdir()
    (docs_dir / "a.md").write_text("basit icerik", encoding="utf-8")

    ingest(docs_dir, database, fake_runtime, chunk_size=200, chunk_overlap=20)

    chunks = database.all_chunks()
    assert all(chunk.page is None for chunk in chunks)
