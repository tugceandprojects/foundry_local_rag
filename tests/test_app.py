from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("streamlit")

from conftest import FakeRuntime
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


@pytest.fixture
def app(tmp_path, monkeypatch):
    import streamlit as st

    docs = tmp_path / "documents"
    docs.mkdir()
    monkeypatch.setenv("RAG_DATABASE", str(tmp_path / "test.db"))
    monkeypatch.setenv("RAG_DOCUMENTS", str(docs))
    monkeypatch.setenv("RAG_MIN_SCORE", "0.0")
    monkeypatch.setattr("local_rag.providers.FoundryLocalRuntime", lambda *a, **k: FakeRuntime())
    st.cache_resource.clear()
    return AppTest.from_file(APP, default_timeout=30), docs


def test_empty_state_renders_without_error_and_input_is_disabled(app):
    at, _docs = app
    at.run()
    assert not at.exception
    assert at.chat_input[0].disabled


def test_index_then_ask_shows_answer_with_source_tab(app):
    at, docs = app
    (docs / "fizik.md").write_text("Newton'un ikinci yasası kuvvet ve ivmeyi ilişkilendirir.", encoding="utf-8")
    at.run()
    index_button = next(b for b in at.sidebar.button if b.label.startswith("Dosyaları indeksle"))
    index_button.click().run()
    assert not at.exception

    at.chat_input[0].set_value("Newton'un ikinci yasası nedir?").run()
    assert not at.exception
    assert len(at.chat_message) == 2
    assert any("fizik.md" in m.value for m in at.markdown)
