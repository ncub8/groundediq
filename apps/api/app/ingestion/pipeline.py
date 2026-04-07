from pathlib import Path

from app.db.repositories.chunks import create_chunk
from app.db.repositories.documents import create_document
from app.db.session import SessionLocal
from app.ingestion.chunker import chunk_text
from app.ingestion.metadata import build_document_metadata, infer_source_type
from app.ingestion.normalizer import normalize_text
from app.ingestion.parsers.docx_parser import DocxParser
from app.ingestion.parsers.markdown_parser import MarkdownParser
from app.ingestion.parsers.pdf_parser import PDFParser
from app.ingestion.parsers.text_parser import TextParser


def get_parser(file_path: Path):
    ext = file_path.suffix.lower()
    if ext == ".pdf":
        return PDFParser()
    if ext == ".docx":
        return DocxParser()
    if ext == ".md":
        return MarkdownParser()
    return TextParser()


def ingest_file(
    file_path: Path,
    domain: str | None = None,
    access_level: str = "internal",
) -> dict:
    parser = get_parser(file_path)
    raw_text = parser.parse(file_path)
    normalized = normalize_text(raw_text)
    chunks = chunk_text(normalized)

    db = SessionLocal()
    try:
        doc = create_document(
            db=db,
            source_name=file_path.name,
            title=file_path.stem,
            source_type=infer_source_type(file_path),
            domain=domain,
            access_level=access_level,
            metadata_json=build_document_metadata(file_path),
        )

        for idx, chunk in enumerate(chunks):
            create_chunk(
                db=db,
                document_id=doc.id,
                chunk_index=idx,
                chunk_text=chunk["text"],
                section_heading=chunk.get("section_heading"),
                token_count=chunk.get("token_count"),
                metadata_json={
                    "filename": file_path.name,
                    "chunk_index": idx,
                },
            )

        db.commit()

        return {
            "document_id": doc.id,
            "source_name": file_path.name,
            "chunk_count": len(chunks),
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()