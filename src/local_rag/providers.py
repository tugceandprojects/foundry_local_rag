"""Microsoft Foundry Local SDK'sını uygulamanın ihtiyaç duyduğu iki basit
işleme (embed / chat) indirgeyen ince bir adaptör katmanı.

Bu dosyanın tek sorumluluğu Foundry Local ile konuşmaktır: model adı ya da
SDK çağrıları değişirse esas olarak burası güncellenir (bkz. PROJE_REHBERI.md,
"Kodun katmanları"). Modeller ilk kullanımda tembel (lazy) olarak indirilip
yüklenir; böylece bu modülü import etmek ya da testleri çalıştırmak Foundry
Local kurulu olmasını gerektirmez.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol


class ModelRuntime(Protocol):
    """`RagService` ve `Retriever`'ın beklediği minimal arayüz.

    Testlerde bu arayüzü uygulayan sahte (fake) bir sınıf kullanılır, böylece
    birim testleri gerçek bir model indirmeden çalışır.
    """

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...

    def chat(self, system_prompt: str, user_prompt: str) -> str: ...


class FoundryLocalRuntime:
    """Foundry Local üzerinde embedding ve sohbet modellerini çalıştırır.

    Embedding'ler için Foundry Local'in yerel (native) embedding istemcisi,
    sohbet için ise Foundry Local'in OpenAI uyumlu yerleşik web servisi
    kullanılır. Bu iki yaklaşım da Microsoft'un resmi dokümantasyonunda
    önerilen entegrasyon yollarıdır.
    """

    def __init__(self, embedding_model: str, chat_model: str):
        self._embedding_model_name = embedding_model
        self._chat_model_name = chat_model
        self._manager: Any = None
        self._embedding_client: Any = None
        self._openai_client: Any = None
        self._chat_model_id: str | None = None

    # -- iç yardımcılar -----------------------------------------------------

    def _ensure_manager(self) -> Any:
        if self._manager is not None:
            return self._manager
        try:
            from foundry_local_sdk import Configuration, FoundryLocalManager
        except ImportError as exc:  # pragma: no cover - sadece SDK kurulu değilse
            raise RuntimeError(
                "foundry-local-sdk kurulu değil. Gerçek çıkarım için "
                "'pip install -e \".[cross-platform]\"' (Windows'ta "
                "'.[windows]') ile kurun."
            ) from exc
        config = Configuration(app_name="yerel_belge_asistani")
        FoundryLocalManager.initialize(config)
        self._manager = FoundryLocalManager.instance
        return self._manager

    def _ensure_embedding_client(self) -> Any:
        if self._embedding_client is not None:
            return self._embedding_client
        manager = self._ensure_manager()
        model = manager.catalog.get_model(self._embedding_model_name)
        model.download(lambda _progress: None)
        model.load()
        self._embedding_client = model.get_embedding_client()
        return self._embedding_client

    def _ensure_chat_client(self) -> tuple[Any, str]:
        if self._openai_client is not None and self._chat_model_id is not None:
            return self._openai_client, self._chat_model_id
        manager = self._ensure_manager()
        model = manager.catalog.get_model(self._chat_model_name)
        model.download(lambda _progress: None)
        model.load()
        manager.start_web_service()
        import openai

        base_url = manager.urls[0] if getattr(manager, "urls", None) else manager.endpoint
        self._openai_client = openai.OpenAI(base_url=base_url, api_key="not-needed")
        self._chat_model_id = model.model_id
        return self._openai_client, self._chat_model_id

    # -- genel arayüz ---------------------------------------------------------

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        texts = list(texts)
        if not texts:
            return []
        client = self._ensure_embedding_client()
        response = client.generate_embeddings(texts)
        return [item.embedding for item in response.data]

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        client, model_id = self._ensure_chat_client()
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""
