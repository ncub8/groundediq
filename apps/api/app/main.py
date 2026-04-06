from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import Base, engine
from app.db import models  # noqa: F401
from app.routes.ingest import router as ingest_router

app = FastAPI(title="GroundedIQ API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


app.include_router(ingest_router)


@app.get("/health")
def health():
    return {"status": "ok"}