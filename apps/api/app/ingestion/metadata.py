from pathlib import Path
from typing import Any, Dict


def build_document_metadata(file_path: Path) -> Dict[str, Any]:
    return {
        "filename": file_path.name,
        "extension": file_path.suffix.lower(),
    }


def infer_source_type(file_path: Path) -> str:
    ext = file_path.suffix.lower()
    if ext == ".pdf":
        return "pdf"
    if ext == ".docx":
        return "docx"
    if ext == ".md":
        return "markdown"
    return "text"