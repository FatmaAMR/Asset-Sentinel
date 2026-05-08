from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# يفضل جداً زي ما اتفقنا إن اللينك ده يتقرأ من ملف .env بعدين
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:123456@localhost:5432/sentinel_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()