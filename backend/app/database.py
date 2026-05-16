from sqlalchemy import create_backend, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.db.session import SessionLocal


# Helper (Dependency Injection) para abrir y cerrar la sesión de BD en cada request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()