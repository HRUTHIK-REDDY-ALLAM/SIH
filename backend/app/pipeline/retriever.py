"""Retrieval layer for RAG-grounded compliance reasoning.

The compliance node does not rely on unguided model knowledge: it retrieves
passages from a small curated corpus of regulatory summaries (app/regs/) and
cites them — doc ID + section — in the trace and the decision record, so every
compliance statement is traceable to a source passage.

The `Retriever` port is deliberately minimal. This implementation is BM25
(rank_bm25) over section-level chunks — deterministic, dependency-light, and
offline. # PRODUCTION SWAP: implement the same interface over a vector store
(FAISS / Weaviate / pgvector) with embedding search; nothing else changes.
"""
import re
from dataclasses import dataclass
from pathlib import Path

from rank_bm25 import BM25Okapi

REGS_DIR = Path(__file__).resolve().parent.parent / "regs"


@dataclass
class Passage:
    doc_id: str
    doc_title: str
    section: str
    text: str

    @property
    def ref(self) -> str:
        return f"{self.doc_id} {self.section}"


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class Retriever:
    def search(self, query: str, k: int = 2) -> list[Passage]:
        raise NotImplementedError


class BM25Retriever(Retriever):
    def __init__(self, regs_dir: Path = REGS_DIR):
        self.passages: list[Passage] = []
        for path in sorted(regs_dir.glob("*.md")):
            doc_id, doc_title = "", path.stem
            body_sections: list[tuple[str, list[str]]] = []
            current = None
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.startswith("# ") and not doc_id:
                    head = line[2:].strip()
                    doc_id = head.split(" — ")[0].strip()
                    doc_title = head.split(" — ")[-1].strip()
                elif line.startswith("## "):
                    current = (line[3:].strip(), [])
                    body_sections.append(current)
                elif current is not None and line.strip() and not line.startswith(">"):
                    current[1].append(line.strip())
            for section, lines in body_sections:
                text = " ".join(lines)
                if text:
                    self.passages.append(Passage(doc_id=doc_id, doc_title=doc_title,
                                                 section=section.split(" ")[0], text=text))
        self._bm25 = BM25Okapi([_tokenize(p.text + " " + p.doc_title) for p in self.passages])

    def search(self, query: str, k: int = 2) -> list[Passage]:
        scores = self._bm25.get_scores(_tokenize(query))
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        return [self.passages[i] for i in ranked[:k] if scores[i] > 0]


_retriever: Retriever | None = None


def get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = BM25Retriever()
    return _retriever
