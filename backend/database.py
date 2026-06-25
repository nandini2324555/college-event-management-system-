import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ✅ IMPORTANT FIX: use PostgreSQL from Render
DATABASE_URL = os.getenv("DATABASE_URL")
print("DATABASE_URL =", DATABASE_URL)

# fallback (local development)
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./events.db"

# PostgreSQL case
if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(DATABASE_URL)
else:
    # SQLite case (local only)
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()