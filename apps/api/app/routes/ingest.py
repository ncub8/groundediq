from pathlib import Path

from fastapi import APIRouter
from app.ingestion.pipeline import ingest_file
from app.schemas.ingest import IngestRequest

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("")
def ingest(request: IngestRequest):
    result = ingest_file(
        file_path=Path(request.file_path),
        domain=request.domain,
        access_level=request.access_level,
    )
    return result