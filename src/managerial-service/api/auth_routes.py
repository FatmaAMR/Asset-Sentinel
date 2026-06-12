from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from services.logic import StaffLogic
from services.security import create_access_token, get_current_user
from schemas.models import Token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await StaffLogic.authenticate_user(form_data.username, form_data.password)
    access_token = create_access_token(
        data={"sub": user["email"], "role": user["role"]}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: dict = Depends(get_current_user),
):
    return await StaffLogic.change_staff_password(
        email=current_user["email"],
        old_pw=old_password,
        new_pw=new_password,
    )