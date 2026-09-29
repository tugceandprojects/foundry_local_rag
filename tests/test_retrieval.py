from __future__ import annotations

from local_rag.retrieval import Retriever, cosine_similarity


def test_cosine_similarity_identical_vectors_is_one():
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0


def test_cosine_similarity_orthogonal_vectors_is_zero():
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_cosine_similarity_handles_zero_vector():
    assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0


def test_cosine_similarity_mismatched_lengths_returns_zero():
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0, 0.0]) == 0.0


def test_retriever_returns_empty_list_when_database_is_empty(database, fake_runtime):
    retriever = Retriever(database, fake_runtime)
    assert retriever.retrieve("herhangi bir soru", top_k=3) == []


def test_retriever_ranks_most_similar_chunk_first(database, fake_runtime):
    # Aynı metne çok benzeyen bir bölüm en üstte çıkmalı.
    target_text = "Foundry Local çevrimdışı çalışan bir model çalışma zamanıdır"
    unrelated_text = "kedi köpek balık kuş"

    database.add_chunk("a.md", 0, target_text, fake_runtime.embed([target_text])[0])
    database.add_chunk("b.md", 0, unrelated_text, fake_runtime.embed([unrelated_text])[0])

    retriever = Retriever(database, fake_runtime)
    results = retriever.retrieve(target_text, top_k=2)

    assert len(results) == 2
    assert results[0].source == "a.md"
    assert results[0].score >= results[1].score


def test_retriever_respects_top_k(database, fake_runtime):
    for i in range(5):
        text = f"bölüm numarası {i}"
        database.add_chunk("a.md", i, text, fake_runtime.embed([text])[0])

    retriever = Retriever(database, fake_runtime)
    results = retriever.retrieve("bölüm numarası 2", top_k=2)
    assert len(results) == 2
