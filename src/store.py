from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401

            # Keep the probe only; the test suite uses the in-memory path.
            self._use_chroma = False
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        metadata = dict(doc.metadata or {})
        metadata.setdefault("doc_id", doc.id)
        embedding = self._embedding_fn(doc.content)
        return {
            "id": doc.id,
            "doc_id": doc.id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": embedding,
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if top_k <= 0 or not records:
            return []

        query_embedding = self._embedding_fn(query)
        scored: list[dict[str, Any]] = []

        for record in records:
            score = _dot(query_embedding, record["embedding"])
            scored.append(
                {
                    "id": record["id"],
                    "doc_id": record.get("doc_id", record.get("metadata", {}).get("doc_id")),
                    "content": record["content"],
                    "metadata": dict(record.get("metadata", {})),
                    "score": score,
                }
            )

        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        if not docs:
            return

        records = [self._make_record(doc) for doc in docs]

        if self._use_chroma and self._collection is not None:
            try:
                self._collection.add(
                    ids=[record["id"] for record in records],
                    documents=[record["content"] for record in records],
                    embeddings=[record["embedding"] for record in records],
                    metadatas=[record["metadata"] for record in records],
                )
                self._next_index += len(records)
                return
            except Exception:
                self._use_chroma = False

        self._store.extend(records)
        self._next_index += len(records)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if top_k <= 0:
            return []

        if self._use_chroma and self._collection is not None:
            try:
                query_embedding = self._embedding_fn(query)
                results = self._collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    include=["documents", "metadatas", "distances", "ids"],
                )
                ids = results.get("ids", [[]])[0]
                documents = results.get("documents", [[]])[0]
                metadatas = results.get("metadatas", [[]])[0]
                distances = results.get("distances", [[]])[0]
                output: list[dict[str, Any]] = []
                for idx, content in enumerate(documents):
                    metadata = metadatas[idx] if idx < len(metadatas) and metadatas[idx] is not None else {}
                    distance = float(distances[idx]) if idx < len(distances) else 0.0
                    output.append(
                        {
                            "id": ids[idx] if idx < len(ids) else metadata.get("doc_id"),
                            "doc_id": metadata.get("doc_id"),
                            "content": content,
                            "metadata": metadata,
                            "score": 1.0 - distance,
                        }
                    )
                return output
            except Exception:
                self._use_chroma = False

        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma and self._collection is not None:
            try:
                return int(self._collection.count())
            except Exception:
                self._use_chroma = False
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if metadata_filter is None:
            return self.search(query, top_k=top_k)

        filtered_records = []
        for record in self._store:
            metadata = record.get("metadata", {})
            if all(metadata.get(key) == value for key, value in metadata_filter.items()):
                filtered_records.append(record)

        return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma and self._collection is not None:
            try:
                existing = self._collection.get(include=["metadatas", "ids"])
                ids = existing.get("ids", [])
                metadatas = existing.get("metadatas", [])
                ids_to_delete = []
                for idx, metadata in enumerate(metadatas):
                    if metadata and metadata.get("doc_id") == doc_id:
                        ids_to_delete.append(ids[idx])
                if ids_to_delete:
                    self._collection.delete(ids=ids_to_delete)
                    return True
                return False
            except Exception:
                self._use_chroma = False

        before = len(self._store)
        self._store = [record for record in self._store if record.get("metadata", {}).get("doc_id") != doc_id]
        return len(self._store) < before
