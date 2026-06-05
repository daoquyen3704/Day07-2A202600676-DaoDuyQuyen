from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from src import Document, EmbeddingStore, OpenAIEmbedder


DEFAULT_DATASET_DIR = Path("data")
ALLOWED_RECIPE_FILES = {
    "pho_bo.md",
    "bun_rieu.md",
    "canh_chua_ca.md",
    "ga_chien_nuoc_mam.md",
    "rau_muong_xao_toi.md",
    "che_dau_xanh.md",
    "banh_flan.md",
    "meo_nau_nuoc_dung.md",
    "cach_so_che_nguyen_lieu.md",
    "dinh_luong_gia_vi_co_ban.md",
}


def parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    """
    Parse a simple YAML-like frontmatter block from a markdown file.

    Supports:
    - quoted or unquoted scalar values
    - inline lists: [a, b, c]
    """
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

        if value == "":
            collected: list[str] = []
            i += 1
            while i < len(lines) and lines[i].startswith("  - "):
                item = lines[i].strip()[2:].strip()
                item = item.strip().strip('"').strip("'")
                collected.append(item)
                i += 1
            metadata[key] = collected
            continue

        if value.startswith("[") and value.endswith("]"):
            items = [item.strip().strip('"').strip("'") for item in value[1:-1].split(",") if item.strip()]
            metadata[key] = items
        else:
            metadata[key] = value.strip('"').strip("'")
        i += 1

    return metadata, body


def load_recipe_documents(dataset_dir: Path = DEFAULT_DATASET_DIR) -> list[Document]:
    documents: list[Document] = []

    for file_path in sorted(dataset_dir.glob("*.md")):
        if file_path.name == "README.md" or file_path.name not in ALLOWED_RECIPE_FILES:
            continue

        text = file_path.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(text)
        metadata = dict(metadata)
        metadata.setdefault("doc_id", file_path.stem)
        metadata.setdefault("source_file", file_path.name)
        metadata.setdefault("title", file_path.stem.replace("_", " "))

        documents.append(
            Document(
                id=file_path.stem,
                content=body.strip(),
                metadata=metadata,
            )
        )

    return documents


def build_recipe_store(dataset_dir: Path = DEFAULT_DATASET_DIR) -> EmbeddingStore:
    docs = load_recipe_documents(dataset_dir)
    embedder = OpenAIEmbedder(model_name=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"))
    store = EmbeddingStore(collection_name="recipe_vector_dataset", embedding_fn=embedder)
    store.add_documents(docs)
    return store


def main() -> int:
    parser = argparse.ArgumentParser(description="Load recipe documents with frontmatter metadata and optionally run a search demo.")
    parser.add_argument("--query", type=str, default="", help="Optional query to test retrieval.")
    parser.add_argument("--top-k", type=int, default=3, help="Number of results to show.")
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=DEFAULT_DATASET_DIR,
        help="Path to the data directory containing recipe markdown files.",
    )
    args = parser.parse_args()

    docs = load_recipe_documents(args.dataset_dir)
    print(f"Loaded {len(docs)} documents from {args.dataset_dir}")
    for doc in docs:
        print(f"- {doc.id}: {doc.metadata.get('title', doc.id)}")

    if not args.query.strip():
        return 0

    store = build_recipe_store(args.dataset_dir)
    results = store.search(args.query, top_k=args.top_k)
    print(f"\nQuery: {args.query}")
    for idx, result in enumerate(results, start=1):
        title = result["metadata"].get("title", result["id"])
        print(f"{idx}. score={result['score']:.4f} title={title}")
        preview = result["content"][:140].replace("\n", " ")
        print(f"   {preview}...")

    return 0


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv(override=True)
    raise SystemExit(main())
