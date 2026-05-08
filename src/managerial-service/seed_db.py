from database import SessionLocal
from db_models import DBStaff
from services.security import get_password_hash
import uuid
from datetime import datetime

def seed_admin():
    db = SessionLocal()
    # نتأكد إننا مكررناش اليوزر
    check_user = db.query(DBStaff).filter(DBStaff.email == "ezz@factory.com").first()
    
    if not check_user:
        admin_user = DBStaff(
            staff_id=f"EMP-001",
            full_name="Ezz Ahmed",
            role="Admin",
            email="ezz@factory.com",
            password=get_password_hash("123456"), # الباسورد بتاعك
            created_at=datetime.utcnow().strftime("%Y-%m-%d")
        )
        db.add(admin_user)
        db.commit()
        print("✅ Admin user created successfully!")
    else:
        print("⚠️ Admin user already exists.")
    db.close()

if __name__ == "__main__":
    seed_admin()