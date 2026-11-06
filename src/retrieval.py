"""TF-IDF retrieval over the sample knowledge-base docs.

Standard library only (``re``, ``math``, ``collections``) so the demo mode
runs with no third-party dependencies. Documents are split into paragraph
chunks; each chunk is scored against the query with cosine similarity over
TF-IDF vectors.
"""
import math
import re
from collections import Counter
from pathlib import Path

STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "with",
    "is", "are", "was", "were", "be", "by", "at", "from", "it", "its",
    "i", "you", "your", "my", "me", "we", "how", "do", "does", "did",
    "what", "when", "where", "who", "can", "could", "should", "would",
    "please", "if", "then", "than", "as", "this", "that", "there", "here",
    "am", "have", "has", "had", "not", "no", "but", "so", "up", "out",
}


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens with stopwords removed."""
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOPWORDS]


class Chunk:
    """One retrievable unit of a knowledge-base document."""

    def __init__(self, source: str, text: str):
        self.source = source
        self.text = text.strip()

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Chunk({self.source!r}, {self.text[:40]!r}...)"


class TfIdfRetriever:
    """Build a TF-IDF index over ``docs_dir`` and retrieve top-k chunks."""

    def __init__(self, docs_dir: str = "data/sample_docs"):
        self.docs_dir = Path(docs_dir)
        self.chunks: list[Chunk] = []
        self._idf: dict[str, float] = {}
        self._chunk_vectors: list[dict[str, float]] = []
        self._build()

    def _load_chunks(self) -> None:
        for path in sorted(self.docs_dir.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            # Split on blank lines / headings; drop the fictional-doc notice.
            parts = re.split(r"\n\s*\n", text)
            for part in parts:
                part = part.strip()
                if not part or part.startswith("> Fictional"):
                    continue
                if part.startswith("#"):
                    # Heading-only chunk (doc title / section heading):
                    # headings contain the query terms but no facts, and
                    # picking them as "sentences" produces heading salad
                    # in extractive answers (and inflates TF-IDF scores).
                    continue
                # Strip markdown heading markers but keep the heading text.
                part = re.sub(r"^#+\s*", "", part, flags=re.MULTILINE)
                self.chunks.append(Chunk(source=path.name, text=part))

    def _build(self) -> None:
        self._load_chunks()
        n = len(self.chunks)
        doc_freq: Counter = Counter()
        chunk_tokens: list[list[str]] = []
        for chunk in self.chunks:
            tokens = tokenize(chunk.text)
            chunk_tokens.append(tokens)
            for token in set(tokens):
                doc_freq[token] += 1
        self._idf = {
            token: math.log((n + 1) / (df + 1)) + 1.0
            for token, df in doc_freq.items()
        }
        for tokens in chunk_tokens:
            counts = Counter(tokens)
            total = len(tokens) or 1
            vec = {
                token: (count / total) * self._idf.get(token, 1.0)
                for token, count in counts.items()
            }
            self._chunk_vectors.append(vec)

    def _query_vector(self, query: str) -> dict[str, float]:
        counts = Counter(tokenize(query))
        total = sum(counts.values()) or 1
        return {
            token: (count / total) * self._idf.get(token, math.log(len(self.chunks) + 1) + 1.0)
            for token, count in counts.items()
        }

    @staticmethod
    def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
        dot = sum(a[t] * b.get(t, 0.0) for t in a)
        norm_a = math.sqrt(sum(v * v for v in a.values()))
        norm_b = math.sqrt(sum(v * v for v in b.values()))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def retrieve(self, query: str, top_k: int = 3) -> list[dict]:
        """Return the top-k chunks as ``{source, text, score}`` dicts."""
        qvec = self._query_vector(query)
        scored = [
            {"source": chunk.source, "text": chunk.text,
             "score": self._cosine(qvec, vec)}
            for chunk, vec in zip(self.chunks, self._chunk_vectors)
        ]
        scored.sort(key=lambda r: r["score"], reverse=True)
        return scored[:top_k]
