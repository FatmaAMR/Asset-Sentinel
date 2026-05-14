from fastapi import APIRouter, status, Depends
from sqlalchemy.orm import Session # إضافة جديدة
from typing import List
from schemas.models import StaffCreate, StaffResponse
from services.logic import StaffLogic
from db.connection import get_db
from db.models import DBStaff
from services.security import verify_password, create_access_token
from services.security import get_current_user, require_role

router = APIRouter(prefix="/staff", tags=["Staff Management"])

# ── أي حد logged in يشوف الـ staff ──
@router.get("/", response_model=List[StaffResponse])
async def get_staff(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db) # فتح اتصال الداتا بيز
):
    return StaffLogic.list_all_staff(db) # باصينا الـ db

# ── Admin بس يضيف staff ──
@router.post("/", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
async def create_staff(
    staff: StaffCreate,
    current_user: dict = Depends(require_role("Admin")),
    db: Session = Depends(get_db) # فتح اتصال الداتا بيز
):
    return StaffLogic.add_staff(staff, db) # باصينا الـ db

@router.get("/all")
async def get_all_staff_internal(db: Session = Depends(get_db)):
    staff = StaffLogic.list_all_staff(db)
    return {
        "users": [
            {"name": s.full_name, "email": s.email, "role": s.role}
            for s in staff
        ]
    }

# ── أي حد logged in يشوف staff معين ──
@router.get("/{staff_id}", response_model=StaffResponse)
async def get_staff_by_id(
    staff_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db) # فتح اتصال الداتا بيز
):
    return StaffLogic.get_staff_by_id(staff_id, db) # باصينا الـ db

# ── Admin و Manager يعدلوا staff ──
@router.put("/{staff_id}", response_model=StaffResponse)
async def update_staff(
    staff_id: str,
    staff: StaffCreate,
    current_user: dict = Depends(require_role("Admin", "Manager")),
    db: Session = Depends(get_db) # فتح اتصال الداتا بيز
):
    return StaffLogic.update_staff(staff_id, staff, db) # باصينا الـ db

# ── Admin بس يمسح staff ──
@router.delete("/{staff_id}")
async def delete_staff(
    staff_id: str,
    current_user: dict = Depends(require_role("Admin")),
    db: Session = Depends(get_db) # فتح اتصال الداتا بيز
):
    return StaffLogic.remove_staff(staff_id, db) # باصينا الـ db

