from pathlib import Path
from pypdf import PdfReader
from app.ingestion.parsers.base import BaseParser


class PDFParser(BaseParser):
    def parse(self, file_path: Path) -> str:
        reader = PdfReader(str(file_path))
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n".join(pages)