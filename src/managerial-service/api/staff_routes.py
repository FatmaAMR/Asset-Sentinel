from fastapi import APIRouter, status, Depends
from typing import List
from schemas.models import StaffCreate, StaffResponse
from services.logic import StaffLogic
from services.security import get_current_user, require_role

router = APIRouter(prefix="/staff", tags=["Staff Management"])

@router.get("/all")
async def get_all_staff_internal():
    staff = await StaffLogic.list_all_staff()
    return {
        "users": [
            {"name": s["full_name"], "email": s["email"], "role": s["role"]}
            for s in staff
        ]
    }

@router.get("/", response_model=List[StaffResponse])
async def get_staff(current_user: dict = Depends(get_current_user)):
    return await StaffLogic.list_all_staff()

@router.post("/", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
async def create_staff(
    staff: StaffCreate,
    current_user: dict = Depends(require_role("Admin")),
):
    return await StaffLogic.add_staff(staff)

@router.get("/{staff_id}", response_model=StaffResponse)
async def get_staff_by_id(
    staff_id: str,
    current_user: dict = Depends(get_current_user),
):
    return await StaffLogic.get_staff_by_id(staff_id)

@router.put("/{staff_id}", response_model=StaffResponse)
async def update_staff(
    staff_id: str,
    staff: StaffCreate,
    current_user: dict = Depends(require_role("Admin", "Manager")),

):
    return await StaffLogic.update_staff(staff_id, staff)

@router.delete("/{staff_id}")
async def delete_staff(
    staff_id: str,
    current_user: dict = Depends(require_role("Admin")),

):
    return await StaffLogic.remove_staff(staff_id)