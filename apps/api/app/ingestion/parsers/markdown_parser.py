from pathlib import Path
from app.ingestion.parsers.base import BaseParser


class MarkdownParser(BaseParser):
    def parse(self, file_path: Path) -> str:
        return file_path.read_text(encoding="utf-8")