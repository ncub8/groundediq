from sqlalchemy.orm import Session
from app.db.models import Document


def create_document(
    db: Session,
    source_name: str,
    title: str,
    source_type: str,
    domain: str | None,
    access_level: str,
    metadata_json: dict | None,
) -> Document:
    document = Document(
        source_name=source_name,
        title=title,
        source_type=source_type,
        domain=domain,
        access_level=access_level,
        metadata_json=metadata_json,
    )
    db.add(document)
    db.flush()
    return document