"""`local-rag ingest` ve `local-rag chat` komutlarını sağlayan CLI."""

from __future__ import annotations

import argparse
import sys

from .config import Settings
from .database import KnowledgeDatabase
from .ingestion import ingest
from .providers import FoundryLocalRuntime
from .retrieval import Retriever
from .service import RagService


def _build_service(settings: Settings, runtime: FoundryLocalRuntime, database: KnowledgeDatabase) -> RagService:
    return RagService(Retriever(database, runtime), runtime, settings.top_k, settings.min_score)


def run_ingest(settings: Settings) -> None:
    database = KnowledgeDatabase(settings.database_path)
    database.initialize()
    runtime = FoundryLocalRuntime(settings.embedding_model, settings.chat_model)
    print(f"'{settings.documents_path}' klasöründeki belgeler indeksleniyor...")
    count = ingest(settings.documents_path, database, runtime, settings.chunk_size, settings.chunk_overlap)
    print(f"{count} bölüm indekslendi.")


def run_chat(settings: Settings) -> None:
    database = KnowledgeDatabase(settings.database_path)
    database.initialize()
    if database.count() == 0:
        print("Bilgi tabanı boş. Önce 'local-rag ingest' komutunu çalıştırın.")
        return

    runtime = FoundryLocalRuntime(settings.embedding_model, settings.chat_model)
    service = _build_service(settings, runtime, database)

    print("Sorularınızı yazın (çıkmak için 'exit').")
    while True:
        try:
            question = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue

        answer = service.answer(question)
        print(answer.text)
        for source in answer.sources:
            location = f"sayfa {source.page}" if source.page is not None else f"bölüm {source.position + 1}"
            print(f"  - {source.source} ({location}, benzerlik {source.score:.3f})")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="local-rag", description="Yerel Belge Asistanı CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("ingest", help="documents/ klasörünü indeksle")
    subparsers.add_parser("chat", help="Konsolda sohbet moduna gir")

    args = parser.parse_args(argv)
    settings = Settings.from_env()

    if args.command == "ingest":
        run_ingest(settings)
    elif args.command == "chat":
        run_chat(settings)
    return 0


if __name__ == "__main__":
    sys.exit(main())
