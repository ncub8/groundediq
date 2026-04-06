import sys
from pathlib import Path

# Get the API root directory (parent of scripts)
API_ROOT = Path(__file__).resolve().parent.parent
# Get the project root (grandparent of apps/api)
PROJECT_ROOT = API_ROOT.parent.parent

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.ingestion.pipeline import ingest_file  # noqa: E402


def main():
    raw_dir = PROJECT_ROOT / "sample_data" / "raw"

    supported = {".txt", ".md", ".pdf", ".docx"}

    files = [f for f in raw_dir.iterdir() if f.is_file() and f.suffix.lower() in supported]

    if not files:
        print("No supported files found in sample_data/raw")
        return

    for file_path in files:
        result = ingest_file(file_path, domain="claims", access_level="internal")
        print(f"Ingested {file_path.name}: {result}")


if __name__ == "__main__":
    main()