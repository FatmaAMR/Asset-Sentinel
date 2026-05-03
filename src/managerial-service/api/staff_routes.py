from fastapi import APIRouter, status, Depends
from typing import List
from schemas.models import StaffCreate, StaffResponse
from services.logic import StaffLogic
from services.security import get_current_user, require_role

router = APIRouter(prefix="/staff", tags=["Staff Management"])

# ── أي حد logged in يشوف الـ staff ──
@router.get("/", response_model=List[StaffResponse])
async def get_staff(current_user: dict = Depends(get_current_user)):
    return StaffLogic.list_all_staff()

# ── Admin بس يضيف staff ──
@router.post("/", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
async def create_staff(
    staff: StaffCreate,
    current_user: dict = Depends(require_role("Admin"))
):
    return StaffLogic.add_staff(staff)

# ── أي حد logged in يشوف staff معين ──
@router.get("/{staff_id}", response_model=StaffResponse)
async def get_staff_by_id(
    staff_id: str,
    current_user: dict = Depends(get_current_user)
):
    return StaffLogic.get_staff_by_id(staff_id)

# ── Admin و Manager يعدلوا staff ──
@router.put("/{staff_id}", response_model=StaffResponse)
async def update_staff(
    staff_id: str,
    staff: StaffCreate,
    current_user: dict = Depends(require_role("Admin", "Manager"))
):
    return StaffLogic.update_staff(staff_id, staff)

# ── Admin بس يمسح staff ──
@router.delete("/{staff_id}")
async def delete_staff(
    staff_id: str,
    current_user: dict = Depends(require_role("Admin"))
):
    return StaffLogic.remove_staff(staff_id)