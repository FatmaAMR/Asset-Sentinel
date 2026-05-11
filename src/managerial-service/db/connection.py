import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. تحديد مسار ملف الـ .env بدقة (بيرجع خطوة لورا من فولدر db عشان يلاقي الملف)
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"

# 2. تحميل المتغيرات من الملف
load_dotenv(dotenv_path=env_path)

# 3. سحب رابط الداتا بيز من البيئة
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# سطر حماية: لو مش عارف يقرأ اللينك هيطلعلك رسالة واضحة بدل ما يضرب Error غريب
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError(
        "🚨 لم يتم العثور على DATABASE_URL! \n"
        "تأكد من وجود ملف .env داخل فولدر managerial-service \n"
        f"المسار المتوقع للملف هو: {env_path}"
    )

# 4. إنشاء محرك الداتا بيز والجلسات (Sessions)
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 5. دالة الحصول على الـ DB (Dependency Injection)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()