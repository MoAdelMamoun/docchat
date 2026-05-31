"""A pure-Python BM25 retrieval index — no dependencies, fully offline.

We tokenize each chunk, build term/document-frequency tables, and score a query
against every chunk with the Okapi BM25 ranking function. There are no model
downloads and no network: this is classic, transparent keyword retrieval.
"""
import math
import re
from collections import Counter

# A small English stop-word list so common words don't dominate scoring.
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have",
    "how", "i", "in", "is", "it", "its", "of", "on", "or", "our", "that", "the",
    "to", "was", "were", "what", "when", "where", "which", "who", "will", "with",
    "you", "your", "do", "does", "can", "we", "this", "these", "those", "if",
}

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall(text.lower())
            if t not in STOPWORDS and len(t) > 1]


class BM25Index:
    """In-memory BM25 over a list of records, each at least {'id', 'text'}."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.records: list[dict] = []
        self.tokens: list[list[str]] = []
        self.doc_freq: Counter = Counter()
        self.idf: dict[str, float] = {}
        self.avgdl: float = 0.0

    def build(self, records: list[dict]) -> None:
        self.records = records
        self.tokens = [tokenize(r["text"]) for r in records]
        self.doc_freq = Counter()
        for toks in self.tokens:
            for term in set(toks):
                self.doc_freq[term] += 1
        n = len(records)
        self.avgdl = (sum(len(t) for t in self.tokens) / n) if n else 0.0
        # BM25 idf with the usual +1 smoothing (always positive).
        self.idf = {
            term: math.log(1 + (n - df + 0.5) / (df + 0.5))
            for term, df in self.doc_freq.items()
        }

    def _score(self, q_terms: list[str], idx: int) -> float:
        toks = self.tokens[idx]
        if not toks:
            return 0.0
        tf = Counter(toks)
        dl = len(toks)
        score = 0.0
        for term in q_terms:
            if term not in tf:
                continue
            idf = self.idf.get(term, 0.0)
            freq = tf[term]
            denom = freq + self.k1 * (1 - self.b + self.b * dl / (self.avgdl or 1))
            score += idf * (freq * (self.k1 + 1)) / denom
        return score

    def search(self, query: str, top_k: int = 4) -> list[dict]:
        """Return up to top_k records with a positive score, best first."""
        q_terms = tokenize(query)
        if not q_terms or not self.records:
            return []
        scored = []
        for idx in range(len(self.records)):
            s = self._score(q_terms, idx)
            if s > 0:
                rec = dict(self.records[idx])
                rec["score"] = round(s, 4)
                scored.append(rec)
        scored.sort(key=lambda r: r["score"], reverse=True)
        return scored[:top_k]
