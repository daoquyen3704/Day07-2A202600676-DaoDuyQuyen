from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from scripts.load_recipe_dataset import build_recipe_store


BENCHMARKS = [
    {
        "query": "Món nào là món tráng miệng và dùng đậu xanh?",
        "gold_answer": "Chè đậu xanh",
        "metadata_filter": {"category": "dessert", "difficulty": "easy"},
    },
    {
        "query": "Cần bao nhiêu bước để làm Phở bò?",
        "gold_answer": "7 bước",
        "metadata_filter": {"title": "Phở bò"},
    },
    {
        "query": "Món nào có nguyên liệu chính là cá?",
        "gold_answer": "Canh chua cá",
        "metadata_filter": {"category": "soup"},
    },
    {
        "query": "Tài liệu nào thuộc category cooking_tip?",
        "gold_answer": "Mẹo nấu nước dùng; Cách sơ chế nguyên liệu",
        "metadata_filter": {"category": "cooking_tip"},
    },
    {
        "query": "Món nào phù hợp cho bữa sáng?",
        "gold_answer": "Phở bò",
        "metadata_filter": {"meal_type": "breakfast"},
    },
]


def main() -> int:
    store = build_recipe_store()
    print(f"Loaded {store.get_collection_size()} recipe documents")

    for idx, item in enumerate(BENCHMARKS, start=1):
        query = item["query"]
        gold = item["gold_answer"]
        metadata_filter = item["metadata_filter"]

        print(f"\n[{idx}] Query: {query}")
        print(f"Gold: {gold}")

        filtered_results = store.search_with_filter(query, top_k=3, metadata_filter=metadata_filter)
        unfiltered_results = store.search(query, top_k=3)

        print("Filtered top-3:")
        for rank, result in enumerate(filtered_results, start=1):
            print(
                f"  {rank}. score={result['score']:.4f} title={result['metadata'].get('title', result['id'])}"
            )

        print("Unfiltered top-3:")
        for rank, result in enumerate(unfiltered_results, start=1):
            print(
                f"  {rank}. score={result['score']:.4f} title={result['metadata'].get('title', result['id'])}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
