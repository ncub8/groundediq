from pathlib import Path
from docx import Document as DocxDocument
from app.ingestion.parsers.base import BaseParser


class DocxParser(BaseParser):
    def parse(self, file_path: Path) -> str:
        doc = DocxDocument(str(file_path))
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])