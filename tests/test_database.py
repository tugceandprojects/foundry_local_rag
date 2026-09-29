from __future__ import annotations


def test_new_database_is_empty(database):
    assert database.count() == 0
    assert database.all_chunks() == []


def test_add_chunk_and_count(database):
    database.add_chunk("belge1.md", 0, "ilk bölüm", [0.1, 0.2, 0.3])
    database.add_chunk("belge1.md", 1, "ikinci bölüm", [0.4, 0.5, 0.6])
    assert database.count() == 2


def test_all_chunks_roundtrips_embedding(database):
    embedding = [0.1, -0.2, 0.3]
    database.add_chunk("belge1.md", 0, "içerik", embedding)
    stored = database.all_chunks()
    assert len(stored) == 1
    assert stored[0].source == "belge1.md"
    assert stored[0].position == 0
    assert stored[0].content == "içerik"
    assert stored[0].embedding == embedding


def test_clear_all_removes_every_chunk(database):
    database.add_chunk("a.md", 0, "x", [0.0])
    database.add_chunk("b.md", 0, "y", [0.0])
    database.clear_all()
    assert database.count() == 0


def test_clear_source_removes_only_matching_rows(database):
    database.add_chunk("a.md", 0, "x", [0.0])
    database.add_chunk("b.md", 0, "y", [0.0])
    database.clear_source("a.md")
    remaining = database.all_chunks()
    assert len(remaining) == 1
    assert remaining[0].source == "b.md"
