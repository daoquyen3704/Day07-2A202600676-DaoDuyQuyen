from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from src import (
    ChunkingStrategyComparator,
    Document,
    EmbeddingStore,
    KnowledgeBaseAgent,
    OpenAIEmbedder,
    RecursiveChunker,
)


DATA_DIR = Path("data")


def parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    raw_meta = parts[1].strip()
    body = parts[2].lstrip("\r\n")
    metadata: dict[str, object] = {}
    lines = raw_meta.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line or ":" not in line:
            i += 1
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if value.startswith("[") and value.endswith("]"):
            items = [item.strip().strip('"').strip("'") for item in value[1:-1].split(",") if item.strip()]
            metadata[key] = items
        else:
            metadata[key] = value.strip('"').strip("'")
        i += 1

    return metadata, body


def load_documents_with_metadata(data_dir: Path = DATA_DIR) -> list[Document]:
    documents: list[Document] = []
    for filepath in sorted(data_dir.glob("*.md")):
        if filepath.name == "README.md":
            continue
        raw_text = filepath.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(raw_text)
        metadata = dict(metadata)
        metadata.setdefault("doc_id", filepath.stem)
        metadata.setdefault("source_file", filepath.name)
        documents.append(Document(id=filepath.stem, content=body.strip(), metadata=metadata))
    return documents


def pick_embedder():
    return OpenAIEmbedder(model_name=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"))


def run_experiment(strategy_name: str, chunker) -> None:
    print("\n==================================================")
    print(f"BAT DAU CHAY THU NGHIEM: {strategy_name.upper()}")
    print("==================================================")

    docs = load_documents_with_metadata()
    print(f"Da nap {len(docs)} tai lieu tu thu muc data/")

    chunked_docs: list[Document] = []
    for doc in docs:
        chunks = chunker.chunk(doc.content)
        for i, chunk_text in enumerate(chunks):
            chunk_metadata = dict(doc.metadata)
            chunk_metadata["chunk_index"] = i
            chunked_docs.append(
                Document(
                    id=f"{doc.id}_chunk_{i}",
                    content=chunk_text,
                    metadata=chunk_metadata,
                )
            )

    chunk_count = len(chunked_docs)
    avg_length = sum(len(c.content) for c in chunked_docs) / chunk_count if chunk_count else 0.0
    print(f"-> So luong chunk tao ra: {chunk_count}")
    print(f"-> Chieu dai trung binh moi chunk: {avg_length:.1f} ky tu")

    comparator = ChunkingStrategyComparator()
    baseline = comparator.compare(docs[0].content if docs else "", chunk_size=400)
    print("\nBaseline chunking stats (tai lieu dau tien):")
    for name, stats in baseline.items():
        print(f"  - {name}: count={stats['count']}, avg_length={stats['avg_length']:.1f}")

    embedder = pick_embedder()
    print(f"Su dung backend embedding: {getattr(embedder, '_backend_name', embedder.__class__.__name__)}")

    store = EmbeddingStore(collection_name=f"experiment_{strategy_name}", embedding_fn=embedder)
    store.add_documents(chunked_docs)

    def mock_llm(prompt: str) -> str:
        return "[LLM Answer]: Da nhan context va se tra loi dua tren no."

    agent = KnowledgeBaseAgent(store=store, llm_fn=mock_llm)

    benchmark_queries = [
        "Cach lam pho bo truyen thong can nhung nguyen lieu gi?",
        "Lam the nao de nuoc dung trong va khong bi duc?",
        "Cach nau che dau xanh nuoc cot dua tham ngon",
        "Loc rieng thit va xuong heo nhu the nao cho dung cach?",
    ]

    print("\n--- CHAY TRUY VAN THONG THUONG ---")
    for idx, q in enumerate(benchmark_queries, 1):
        print(f"\nQuery {idx}: {q}")
        top_results = store.search(q, top_k=3)
        for r_idx, r in enumerate(top_results, 1):
            print(f"  Top-{r_idx} (Score: {r['score']:.3f}) tu file '{r['metadata'].get('doc_id')}.md'")
            print(f"    Noi dung: {r['content'][:120].replace(chr(10), ' ')}...")
        print("  Agent answer:")
        print(f"    {agent.answer(q, top_k=3)}")

    print("\n--- CHAY TRUY VAN CO DUNG BO LOC METADATA ---")
    filter_query = "Mon canh nao de va phu hop bua trua?"
    metadata_filter = {"category": "soup", "difficulty": "easy", "meal_type": "lunch"}
    print(f"Query: {filter_query}")
    print(f"Filter: {metadata_filter}")
    filtered_results = store.search_with_filter(filter_query, top_k=3, metadata_filter=metadata_filter)
    for r_idx, r in enumerate(filtered_results, 1):
        print(f"  Top-{r_idx} (Score: {r['score']:.3f}) tu file '{r['metadata'].get('doc_id')}.md'")
        print(f"    Noi dung: {r['content'][:120].replace(chr(10), ' ')}...")


if __name__ == "__main__":
    load_dotenv(override=True)
    chunker = RecursiveChunker(chunk_size=400)
    run_experiment("recursive", chunker)
