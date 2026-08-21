import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Database URL using user postgres
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:latharamanan%402005@localhost:5432/careequity"
)

try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True, connect_args={"connect_timeout": 3})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    print(f"Warning: PostgreSQL connection failed ({e}). Running in DB-degraded mode.")
    engine = None
    SessionLocal = None

Base = declarative_base()

def get_db():
    if SessionLocal is None:
        yield None
        return
    
    db = None
    try:
        db = SessionLocal()
        # Test connection validity
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        yield db
    except Exception as err:
        print(f"Database session error: {err}")
        if db is not None:
            try:
                db.close()
            except Exception:
                pass
        yield None
    finally:
        if db is not None:
            try:
                db.close()
            except Exception:
                pass
