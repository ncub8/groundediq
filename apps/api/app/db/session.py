from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# Use environment variable or default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://groundediq:groundediq@localhost:5432/groundediq")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()