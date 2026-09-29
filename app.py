from __future__ import annotations

import html
from pathlib import Path

import streamlit as st

from local_rag.config import Settings
from local_rag.database import KnowledgeDatabase
from local_rag.ingestion import ingest
from local_rag.loaders import SUPPORTED_EXTENSIONS
from local_rag.providers import FoundryLocalRuntime
from local_rag.retrieval import RetrievedChunk, Retriever
from local_rag.service import NO_CONTEXT_MESSAGE, RagService

st.set_page_config(page_title="Ders Çalışma Asistanı", page_icon="📖", layout="centered")
_css = Path(__file__).with_name("styles.css").read_text(encoding="utf-8")
st.markdown(f"<style>{_css}</style>", unsafe_allow_html=True)

st.session_state.setdefault("messages", [])
st.session_state.setdefault("uploader_key", 0)


@st.cache_resource
def create_runtime() -> FoundryLocalRuntime:
    settings = Settings.from_env()
    return FoundryLocalRuntime(settings.embedding_model, settings.chat_model)


settings = Settings.from_env()
database = KnowledgeDatabase(settings.database_path)
database.initialize()


# ---------- yardımcılar ----------


def document_files(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    return sorted(
        p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def safe(text: str) -> str:
    """HTML'e gömülecek metni kaçırır; '$' işaretleri LaTeX sanılmasın diye kodlanır."""
    return html.escape(text).replace("$", "&#36;")


def location(chunk: RetrievedChunk) -> str:
    return f"s. {chunk.page}" if chunk.page is not None else f"bölüm {chunk.position + 1}"


def tab_label(chunk: RetrievedChunk) -> str:
    return f"{chunk.source}, {location(chunk)}"


def show_error(title: str, exc: Exception) -> None:
    st.error(title)
    with st.expander("Teknik ayrıntı"):
        st.exception(exc)


def render_sources(sources: list[RetrievedChunk]) -> None:
    labels = list(dict.fromkeys(tab_label(chunk) for chunk in sources))
    tabs = "".join(f'<span class="tab">{safe(label)}</span>' for label in labels)
    st.markdown(f'<div class="tabs">{tabs}</div>', unsafe_allow_html=True)
    with st.expander("Alıntıları göster"):
        for chunk in sources:
            st.markdown(
                '<div class="passage"><div class="passage-head">'
                f'<span class="tab">{safe(tab_label(chunk))}</span>'
                f'<span class="score">%{round(chunk.score * 100)} eşleşme</span></div>'
                f"<p>{safe(chunk.content)}</p></div>",
                unsafe_allow_html=True,
            )


def render_message(message: dict) -> None:
    if message["role"] == "user":
        with st.chat_message("user"):
            st.markdown(message["text"])
        return
    with st.chat_message("assistant"):
        if message["not_found"]:
            st.markdown(
                f'<div class="notfound"><strong>{safe(message["text"])}</strong>'
                "<span>Soruyu ders notundaki terimlerle yeniden yazmayı dene.</span></div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(message["text"])
            render_sources(message["sources"])


def render_steps(has_files: bool, ready: bool) -> str:
    states = [has_files, ready, False]
    current = next(i for i, done in enumerate(states) if not done)
    items = [
        ("Ders dosyanı ekle", "Sol menüden PDF, TXT veya MD dosyası yükle."),
        (
            "Dosyaları indeksle",
            (
                "Dosyalar sayfa sayfa okunur ve aramaya hazırlanır. İlk seferde modeller "
                "indirilir, birkaç dakika sürebilir."
            ),
        ),
        ("Soru sor", "Cevabın yanında hangi dosyanın hangi sayfasından geldiği görünür."),
    ]
    rows = []
    for i, (title, description) in enumerate(items):
        state = "done" if states[i] else ("now" if i == current else "")
        mark = "✓" if states[i] else str(i + 1)
        rows.append(
            f'<div class="step {state}"><div class="n">{mark}</div>'
            f'<div><p class="t">{title}</p><p class="d">{description}</p></div></div>'
        )
    return f'<div class="steps">{"".join(rows)}</div>'


# ---------- kenar çubuğu ----------

files = document_files(settings.documents_path)
summary = {item.source: item for item in database.sources_summary()}
pending = [path for path in files if path.name not in summary]
ready = database.count() > 0 and not pending

with st.sidebar:
    st.markdown(
        '<div class="brand"><strong>Ders Çalışma Asistanı</strong>'
        "<span>Bu bilgisayarda çalışır. Dosyaların internete gönderilmez.</span></div>",
        unsafe_allow_html=True,
    )

    flash = st.session_state.pop("flash", None)
    if flash:
        st.success(flash)

    st.markdown('<div class="side-title">Ders dosyaların</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "PDF, TXT veya MD ekle",
        type=["pdf", "txt", "md"],
        accept_multiple_files=True,
        key=f"uploader_{st.session_state.uploader_key}",
        label_visibility="collapsed",
    )
    if uploaded:
        settings.documents_path.mkdir(parents=True, exist_ok=True)
        for item in uploaded:
            (settings.documents_path / item.name).write_bytes(item.getvalue())
        st.session_state.uploader_key += 1
        st.session_state.flash = f"{len(uploaded)} dosya eklendi. Şimdi indeksle."
        st.rerun()

    if not files:
        st.markdown(
            '<div class="empty-files">Henüz dosya yok. Yukarıdaki kutuya bir ders PDF\'i '
            "sürükle.</div>",
            unsafe_allow_html=True,
        )
    for path in files:
        info = summary.get(path.name)
        if info is None:
            meta, css = "İndekslenmedi", "meta pending"
        elif info.pages:
            meta, css = f"{info.pages} sayfa, {info.chunks} bölüm", "meta"
        else:
            meta, css = f"{info.chunks} bölüm", "meta"
        left, right = st.columns([5, 2], vertical_alignment="center")
        left.markdown(
            f'<div class="file"><div class="name">{safe(path.name)}</div>'
            f'<div class="{css}">{meta}</div></div>',
            unsafe_allow_html=True,
        )
        if right.button(":material/delete:", key=f"delete_{path}", help="Dosyayı sil"):
            path.unlink(missing_ok=True)
            database.clear_source(path.name)
            st.rerun()

    label = "Dosyaları indeksle"
    if pending:
        label += f" ({len(pending)} yeni)"
    if st.button(
        label,
        type="primary" if not ready else "secondary",
        use_container_width=True,
        disabled=not files,
    ):
        try:
            with st.spinner("Sayfalar okunuyor. İlk seferde modeller indirilir, bekle."):
                count = ingest(
                    settings.documents_path,
                    database,
                    create_runtime(),
                    settings.chunk_size,
                    settings.chunk_overlap,
                )
        except Exception as exc:  # noqa: BLE001 - kullanıcıya anlaşılır hata göstermek için
            show_error("İndeksleme başarısız oldu.", exc)
        else:
            st.session_state.flash = f"{count} bölüm indekslendi. Soru sorabilirsin."
            st.rerun()

    if st.session_state.messages and st.button("Sohbeti temizle", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ---------- ana alan ----------

st.markdown(
    '<div class="hero"><h1>Ders notlarına soru sor</h1>'
    "<p>Cevaplar yalnızca yüklediğin dosyalardan gelir ve hangi sayfadan alındığı "
    "gösterilir.</p></div>",
    unsafe_allow_html=True,
)

intro_slot = st.empty()
if not st.session_state.messages:
    intro_slot.markdown(render_steps(bool(files), ready), unsafe_allow_html=True)

for message in st.session_state.messages:
    render_message(message)

if database.count() == 0:
    placeholder = "Önce soldan dosyalarını indeksle"
elif pending:
    placeholder = "Yeni dosyaları indeksleyince onlara da soru sorabilirsin"
else:
    placeholder = "Ders notlarınla ilgili bir soru yaz"

question = st.chat_input(placeholder, disabled=database.count() == 0)
if question:
    intro_slot.empty()
    user_message = {"role": "user", "text": question}
    st.session_state.messages.append(user_message)
    render_message(user_message)
    try:
        with st.spinner("Notlarında aranıyor..."):
            runtime = create_runtime()
            service = RagService(
                Retriever(database, runtime), runtime, settings.top_k, settings.min_score
            )
            answer = service.answer(question)
    except Exception as exc:  # noqa: BLE001
        with st.chat_message("assistant"):
            show_error("Cevap üretilemedi.", exc)
    else:
        assistant_message = {
            "role": "assistant",
            "text": answer.text,
            "sources": answer.sources,
            "not_found": not answer.sources and answer.text == NO_CONTEXT_MESSAGE,
        }
        st.session_state.messages.append(assistant_message)
        render_message(assistant_message)
