from sqlalchemy.orm import Session
from app.db.models import Chunk


def create_chunk(
    db: Session,
    document_id: int,
    chunk_index: int,
    chunk_text: str,
    section_heading: str | None = None,
    token_count: int | None = None,
    metadata_json: dict | None = None,
) -> Chunk:
    chunk = Chunk(
        document_id=document_id,
        chunk_index=chunk_index,
        section_heading=section_heading,
        chunk_text=chunk_text,
        token_count=token_count,
        metadata_json=metadata_json,
    )
    db.add(chunk)
    return chunk