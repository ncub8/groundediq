from pydantic import BaseModel


class IngestRequest(BaseModel):
    file_path: str
    domain: str | None = None
    access_level: str = "internal"