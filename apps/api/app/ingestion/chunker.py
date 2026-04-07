"""
Semantic chunker for document ingestion.

Strategy:
  1. Detect structural boundaries (headings, section breaks) as hard splits
  2. Split each section into sentences
  3. Build overlapping context windows around each sentence
  4. Embed windows with OpenAI text-embedding-3-small
  5. Compute cosine distance between adjacent windows to find semantic breaks
  6. Group sentences at break points into chunks
  7. Enforce token limits — split oversized chunks, merge undersized ones
  8. Add sentence-level overlap at chunk boundaries to preserve context
"""

import math
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

import tiktoken
from openai import OpenAI

from app.config import settings


# ---------------------------------------------------------------------------
# Structural boundary detection
# ---------------------------------------------------------------------------

# Matches markdown headings, ALL-CAPS headings (≥5 chars), and numbered sections
_HEADING_RE = re.compile(
    r"^(?:#{1,6}\s.+|[A-Z][A-Z\s]{4,}[A-Z]|\d+(?:\.\d+)*\s+[A-Z].+)$",
    re.MULTILINE,
)

# Sentence boundary: ends with . ! ? followed by whitespace + capital letter or quote
_SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?])\s+(?=[A-Z"])')

# Paragraph break — treat as a sentence boundary even within a section
_PARAGRAPH_RE = re.compile(r"\n{2,}")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class ChunkConfig:
    """Tuning knobs for the semantic chunker."""

    # Token budget per chunk (tiktoken cl100k_base).  512 tokens ≈ ~380 words,
    # a good fit for both retrieval precision and answer generation quality.
    max_tokens: int = 512
    # Chunks smaller than this are merged into their neighbour.
    min_tokens: int = 50
    # How many sentences to carry forward from the previous chunk.
    # Preserves cross-boundary context without full character overlap.
    overlap_sentences: int = 1
    # Percentile of cosine-distance values used as the break threshold.
    # Higher → fewer, larger chunks; lower → more, finer-grained chunks.
    breakpoint_percentile: float = 95.0
    # Sentences on each side when building context windows for embedding.
    window_size: int = 2
    # OpenAI embedding model.  text-embedding-3-small lives in the same vector
    # space as retrieval embeddings, keeping similarity scores consistent.
    embedding_model: str = "text-embedding-3-small"
    # tiktoken encoding that matches the embedding model.
    encoding_name: str = "cl100k_base"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def _split_sentences(text: str) -> List[str]:
    """Split text into sentences, also breaking on paragraph boundaries."""
    paragraphs = _PARAGRAPH_RE.split(text)
    sentences: List[str] = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        for part in _SENTENCE_SPLIT_RE.split(para):
            part = part.strip()
            if part:
                sentences.append(part)
    return sentences


def _detect_sections(text: str) -> List[Tuple[int, Optional[str]]]:
    """
    Return (char_offset, heading_or_None) for each structural section.
    The first entry always starts at offset 0.
    """
    headings = [(m.start(), m.group().strip()) for m in _HEADING_RE.finditer(text)]
    if not headings:
        return [(0, None)]

    sections: List[Tuple[int, Optional[str]]] = []
    if headings[0][0] > 0:
        sections.append((0, None))
    for pos, h in headings:
        sections.append((pos, h))
    return sections


def _split_by_structure(text: str) -> List[Dict[str, Any]]:
    """Return [{text, heading, start_char}, …] — one entry per structural section."""
    section_starts = _detect_sections(text)
    result: List[Dict[str, Any]] = []

    for i, (start, heading) in enumerate(section_starts):
        end = section_starts[i + 1][0] if i + 1 < len(section_starts) else len(text)
        body = text[start:end].strip()
        # Remove the heading line itself from the body
        if heading and body.startswith(heading):
            body = body[len(heading):].lstrip()
        if body:
            result.append({"text": body, "heading": heading, "start_char": start})

    return result


def _build_windows(sentences: List[str], window: int) -> List[str]:
    """Create overlapping context windows centred on each sentence."""
    windows = []
    for i in range(len(sentences)):
        lo = max(0, i - window)
        hi = min(len(sentences), i + window + 1)
        windows.append(" ".join(sentences[lo:hi]))
    return windows


def _embed_batch(texts: List[str], model: str, client: OpenAI) -> List[List[float]]:
    if not texts:
        return []
    response = client.embeddings.create(input=texts, model=model)
    ordered = sorted(response.data, key=lambda x: x.index)
    return [item.embedding for item in ordered]


def _find_break_indices(
    embeddings: List[List[float]],
    percentile: float,
) -> Set[int]:
    """
    Return sentence indices AFTER which a semantic break occurs.
    Uses a percentile threshold on pairwise cosine distances so the number
    of breaks scales naturally with document length.
    """
    if len(embeddings) < 2:
        return set()

    distances = [
        1.0 - _cosine_similarity(embeddings[i], embeddings[i + 1])
        for i in range(len(embeddings) - 1)
    ]

    sorted_d = sorted(distances)
    cutoff_idx = min(int(len(sorted_d) * percentile / 100), len(sorted_d) - 1)
    threshold = sorted_d[cutoff_idx]

    return {i for i, d in enumerate(distances) if d >= threshold}


def _group_sentences(sentences: List[str], breaks: Set[int]) -> List[List[str]]:
    groups: List[List[str]] = []
    current: List[str] = []
    for i, sent in enumerate(sentences):
        current.append(sent)
        if i in breaks:
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    return groups


def _enforce_token_limits(
    groups: List[List[str]],
    config: ChunkConfig,
    enc: tiktoken.Encoding,
) -> List[List[str]]:
    """
    Split groups that exceed max_tokens; merge consecutive groups that together
    fit within max_tokens.
    """
    # --- Split oversized groups sentence-by-sentence ---
    split_groups: List[List[str]] = []
    for group in groups:
        tokens = sum(len(enc.encode(s)) for s in group)
        if tokens <= config.max_tokens:
            split_groups.append(group)
            continue

        buf: List[str] = []
        buf_tokens = 0
        for sent in group:
            sent_tokens = len(enc.encode(sent))
            if buf and buf_tokens + sent_tokens > config.max_tokens:
                split_groups.append(buf)
                tail = buf[-config.overlap_sentences:] if config.overlap_sentences else []
                buf = tail + [sent]
                buf_tokens = sum(len(enc.encode(s)) for s in buf)
            else:
                buf.append(sent)
                buf_tokens += sent_tokens
        if buf:
            split_groups.append(buf)

    # --- Merge undersized groups ---
    merged: List[List[str]] = []
    acc: List[str] = []
    acc_tokens = 0
    for group in split_groups:
        group_tokens = sum(len(enc.encode(s)) for s in group)
        if acc and acc_tokens + group_tokens > config.max_tokens:
            merged.append(acc)
            acc = list(group)
            acc_tokens = group_tokens
        else:
            acc.extend(group)
            acc_tokens += group_tokens
    if acc:
        merged.append(acc)

    return merged


def _append_chunk(
    chunks: List[Dict[str, Any]],
    text: str,
    heading: Optional[str],
    index: int,
    enc: tiktoken.Encoding,
    metadata: Optional[Dict[str, Any]],
) -> None:
    text = text.strip()
    if not text:
        return
    chunk: Dict[str, Any] = {
        "text": text,
        "chunk_index": index,
        "section_heading": heading,
        "token_count": len(enc.encode(text)),
    }
    if metadata:
        for k, v in metadata.items():
            if k not in chunk:
                chunk[k] = v
    chunks.append(chunk)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def chunk_text(
    text: str,
    config: Optional[ChunkConfig] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Semantically chunk *text* into a list of chunk dicts.

    Each dict contains:
      - text           : chunk content
      - chunk_index    : zero-based position across the whole document
      - section_heading: nearest structural heading above this chunk, or None
      - token_count    : tiktoken token count
      + any keys from *metadata* (never overrides the above keys)

    Args:
        text:     Normalised document text.
        config:   Chunking parameters (defaults to ChunkConfig()).
        metadata: Extra key/value pairs merged into every chunk dict.
    """
    if not text:
        return []

    if config is None:
        config = ChunkConfig()

    client = OpenAI(api_key=settings.openai_api_key)
    enc = tiktoken.get_encoding(config.encoding_name)

    sections = _split_by_structure(text)
    all_chunks: List[Dict[str, Any]] = []
    chunk_index = 0

    for section in sections:
        body = section["text"]
        heading = section["heading"]

        sentences = _split_sentences(body)
        if not sentences:
            continue

        if len(sentences) == 1:
            _append_chunk(all_chunks, sentences[0], heading, chunk_index, enc, metadata)
            chunk_index += 1
            continue

        # Embed context windows and detect semantic break points
        windows = _build_windows(sentences, config.window_size)
        embeddings = _embed_batch(windows, config.embedding_model, client)
        break_indices = _find_break_indices(embeddings, config.breakpoint_percentile)

        # Group sentences at breaks, then enforce size limits
        groups = _group_sentences(sentences, break_indices)
        groups = _enforce_token_limits(groups, config, enc)

        # Emit chunks with sentence-level overlap carried forward
        overlap_tail: List[str] = []
        for group in groups:
            effective_sentences = overlap_tail + group
            chunk_body = " ".join(effective_sentences)
            _append_chunk(all_chunks, chunk_body, heading, chunk_index, enc, metadata)
            chunk_index += 1
            overlap_tail = group[-config.overlap_sentences:] if config.overlap_sentences else []

    return all_chunks
