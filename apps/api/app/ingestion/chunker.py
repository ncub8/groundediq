import re
from typing import List, Dict, Any


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def chunk_text(
    text: str,
    max_chunk_size: int = 1000,
    overlap: int = 200,
    metadata: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Split text into overlapping chunks for processing.

    Args:
        text: The input text to chunk
        max_chunk_size: Maximum size of each chunk in characters
        overlap: Number of characters to overlap between chunks
        metadata: Additional metadata to include with each chunk

    Returns:
        List of chunk dictionaries with text and metadata
    """
    if not text:
        return []

    chunks = []
    start = 0
    chunk_index = 0

    while start < len(text):
        # Calculate end position
        end = start + max_chunk_size

        # If this isn't the last chunk, try to break at a word boundary
        if end < len(text):
            # Look for the last space within the overlap region
            break_point = text.rfind(' ', start + max_chunk_size - overlap, end)
            if break_point > start:
                end = break_point

        chunk_text = text[start:end].strip()

        if chunk_text:
            chunk = {
                'text': chunk_text,
                'chunk_index': chunk_index,
                'start_char': start,
                'end_char': end,
                'char_count': len(chunk_text)
            }

            # Add any additional metadata
            if metadata:
                chunk.update(metadata)

            chunks.append(chunk)
            chunk_index += 1

        # Move start position with overlap
        start = max(start + 1, end - overlap)

    return chunks