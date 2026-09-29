from __future__ import annotations

from local_rag.retrieval import Retriever
from local_rag.service import NO_CONTEXT_MESSAGE, RagService


def _build_service(database, fake_runtime, top_k=3, min_score=0.35):
    return RagService(Retriever(database, fake_runtime), fake_runtime, top_k, min_score)


def test_empty_question_returns_prompt_without_calling_model(database, fake_runtime):
    service = _build_service(database, fake_runtime)
    answer = service.answer("   ")
    assert answer.text == "Lütfen bir soru yazın."
    assert fake_runtime.chat_calls == []


def test_empty_database_returns_no_context_message(database, fake_runtime):
    service = _build_service(database, fake_runtime)
    answer = service.answer("Foundry Local nedir?")
    assert answer.text == NO_CONTEXT_MESSAGE
    assert answer.sources == []
    assert fake_runtime.chat_calls == []  # eşik altı: model hiç çağrılmamalı


def test_low_similarity_results_are_filtered_out(database, fake_runtime):
    # min_score çok yüksek tutulduğunda hiçbir sonuç eşiği geçemez.
    database.add_chunk("a.md", 0, "alakasız içerik", fake_runtime.embed(["alakasız içerik"])[0])
    service = _build_service(database, fake_runtime, min_score=0.999)
    answer = service.answer("tamamen farklı bir soru")
    assert answer.text == NO_CONTEXT_MESSAGE
    assert fake_runtime.chat_calls == []


def test_relevant_chunk_triggers_model_call_and_returns_sources(database, fake_runtime):
    text = "Foundry Local, modelleri cihaz üzerinde çalıştıran bir çalışma zamanıdır."
    database.add_chunk("foundry.md", 0, text, fake_runtime.embed([text])[0])

    service = _build_service(database, fake_runtime, min_score=0.0)
    answer = service.answer(text)

    assert len(fake_runtime.chat_calls) == 1
    assert answer.sources
    assert answer.sources[0].source == "foundry.md"
    assert "sahte cevap" in answer.text


def test_service_passes_context_in_system_prompt(database, fake_runtime):
    text = "SQLite sunucusuz ve tek dosyalı bir veritabanıdır."
    database.add_chunk("sqlite.md", 0, text, fake_runtime.embed([text])[0])

    service = _build_service(database, fake_runtime, min_score=0.0)
    service.answer(text)

    system_prompt, _user_prompt = fake_runtime.chat_calls[0]
    assert "sqlite.md" in system_prompt
    assert text in system_prompt


def test_pdf_chunks_are_cited_by_page_not_section(database, fake_runtime):
    text = "PDF'ten gelen bir ders notu bölümü."
    database.add_chunk("ders1.pdf", 0, text, fake_runtime.embed([text])[0], page=5)

    service = _build_service(database, fake_runtime, min_score=0.0)
    answer = service.answer(text)

    assert answer.sources[0].page == 5
    system_prompt, _user_prompt = fake_runtime.chat_calls[0]
    assert "sayfa 5" in system_prompt
    assert "bölüm 1" not in system_prompt
