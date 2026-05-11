from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session # إضافة جديدة
from services.logic import StaffLogic 
from services.security import create_access_token, get_current_user
from db.connection import get_db
from db.models import DBStaff
from services.security import verify_password, create_access_token
import traceback
from schemas.models import Token


router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db) # فتحنا ماسورة الداتا بيز
):
    # الروتر بينادي اللوجيك وبيديله الـ db
    user = StaffLogic.authenticate_user(form_data.username, form_data.password, db)

    # تعديل مهم: غيرنا user["email"] لـ user.email عشان ده Object دلوقتي
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/change-password")
def change_password(
    old_password: str,
    new_password: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db) # فتحنا ماسورة الداتا بيز
):
    return StaffLogic.change_staff_password(
        email=current_user["email"], # هنا الداتا جاية من التوكن فبتفضل dict عادي
        old_pw=old_password,
        new_pw=new_password,
        db=db # باصينا الـ db للوجيك
    )