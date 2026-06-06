from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Verify database connection works. Tables should be created via backend/sql/init.sql"""
    from sqlalchemy import text

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        raise Exception(
            f"Cannot connect to database. Error: {str(e)}\n\n"
            "Please ensure:\n"
            "1. PostgreSQL 17 is running on localhost:5432\n"
            "2. eatfit_ai database exists and vector extension is enabled\n\n"
            "To initialize the database, run:\n"
            "PGPASSWORD=root psql -U postgres -h localhost -d eatfit_ai "
            "-f backend/sql/pg/init_pg.sql\n"
            "psql -U postgres -h localhost -d eatfit_ai -c 'CREATE EXTENSION IF NOT EXISTS vector;'\n\n"
            "See README.md for detailed setup instructions."
        )