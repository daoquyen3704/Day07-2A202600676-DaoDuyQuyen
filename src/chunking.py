from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Chia văn bản thành các phần có kích thước cố định với sự chồng chéo tùy chọn

    Quy tắc:
    Mỗi đoạn có độ dài tối đa là các ký tự có kích thước đoạn
    Các đoạn liên tiếp chia sẻ các ký tự chồng chéo
    Đoạn cuối cùng chứa những gì còn lại
    Nếu văn bản ngắn hơn kích thước chunk, hãy trả về [văn bản]
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = max(1, self.chunk_size - self.overlap)
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Chia văn bản thành các đoạn có tối đa số câu tối đa cho mỗi câu đoạn

    Phát hiện câu: phân chia trên " ", "! ", "? " hoặc " \n"
    Loại bỏ khoảng trắng thừa từ mỗi đoạn
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        # Split on sentence-ending punctuation while keeping the punctuation.
        sentence_parts = re.split(r"(?<=[.!?])\s+", text.strip())
        sentences = [part.strip() for part in sentence_parts if part and part.strip()]

        if not sentences:
            return []

        chunks: list[str] = []
        current: list[str] = []

        for sentence in sentences:
            current.append(sentence)
            if len(current) >= self.max_sentences_per_chunk:
                chunks.append(" ".join(current).strip())
                current = []

        if current:
            chunks.append(" ".join(current).strip())

        return chunks


class RecursiveChunker:
    """
    Phân chia văn bản đệ quy bằng dấu phân cách theo thứ tự ưu tiên

    Mức độ ưu tiên của dấu phân cách mặc định:
    ["\n\n", "\n", " ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text.strip(), self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        current_text = current_text.strip()
        if not current_text:
            return []

        if len(current_text) <= self.chunk_size:
            return [current_text]

        if not remaining_separators:
            return FixedSizeChunker(chunk_size=self.chunk_size, overlap=0).chunk(current_text)

        separator = remaining_separators[0]
        if not separator:
            return FixedSizeChunker(chunk_size=self.chunk_size, overlap=0).chunk(current_text)

        if separator not in current_text:
            return self._split(current_text, remaining_separators[1:])

        pieces = [piece.strip() for piece in current_text.split(separator)]
        pieces = [piece for piece in pieces if piece]
        if not pieces:
            return []

        # Rebuild chunks from smaller recursive pieces while keeping them within size.
        joiner = separator if separator.strip() else " "
        chunks: list[str] = []
        buffer = ""

        for piece in pieces:
            subchunks = self._split(piece, remaining_separators[1:])
            for subchunk in subchunks:
                candidate = subchunk if not buffer else f"{buffer}{joiner}{subchunk}"
                if len(candidate) <= self.chunk_size:
                    buffer = candidate
                else:
                    if buffer:
                        chunks.append(buffer)
                    if len(subchunk) <= self.chunk_size:
                        buffer = subchunk
                    else:
                        chunks.extend(FixedSizeChunker(chunk_size=self.chunk_size, overlap=0).chunk(subchunk))
                        buffer = ""

        if buffer:
            chunks.append(buffer)

        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Tính độ tương tự cosin giữa hai vectơ

    độ tương tự cosin = dot(a, b) / (||a|| * ||b||)

    Trả về 0 0 nếu một trong hai vectơ có độ lớn bằng 0
    """
    dot = _dot(vec_a, vec_b)
    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Chạy tất cả các chiến lược chunking được xây dựng sẵn và so sánh kết quả của chúng"""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        fixed_size_chunks = FixedSizeChunker(chunk_size=chunk_size, overlap=min(50, max(0, chunk_size // 10))).chunk(text)
        sentence_chunks = SentenceChunker(max_sentences_per_chunk=max(1, chunk_size // 100)).chunk(text)
        recursive_chunks = RecursiveChunker(chunk_size=chunk_size).chunk(text)

        def summarize(chunks: list[str]) -> dict:
            count = len(chunks)
            avg_length = sum(len(chunk) for chunk in chunks) / count if count else 0.0
            return {
                "count": count,
                "avg_length": avg_length,
                "chunks": chunks,
            }

        return {
            "fixed_size": summarize(fixed_size_chunks),
            "by_sentences": summarize(sentence_chunks),
            "recursive": summarize(recursive_chunks),
        }
