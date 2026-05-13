import sys
import os

# السطر ده بيضمن إن بايثون يشوف الفولدرات اللي جنبه صح
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.connection import SessionLocal
from db.models import DBStaff  # غيرنا db_models لـ models
from services.security import get_password_hash

from datetime import datetime

def seed_admin():
    db = SessionLocal()
    try:
        # بنشيك بالإيميل عشان ميكررش الأدمن كل ما نشغل الملف
        check_user = db.query(DBStaff).filter(DBStaff.email == "ezz@factory.com").first()
        
        if not check_user:
            admin_user = DBStaff(
                staff_id="EMP-001",
                full_name="Ezz Ahmed",
                role="Admin",
                email="ezz@factory.com",
                password=get_password_hash("123456"),
                created_at=datetime.utcnow()
            )
            db.add(admin_user)
            db.commit()
            print("✅ Admin user created successfully!")
        else:
            print("⚠️ Admin user already exists.")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin()