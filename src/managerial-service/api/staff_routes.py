from fastapi import APIRouter, status
from typing import List
from schemas.models import StaffCreate, StaffResponse
from services.logic import StaffLogic

router = APIRouter(prefix="/staff", tags=["Staff Management"])

@router.get("/", response_model=List[StaffResponse])
async def get_staff():
    return StaffLogic.list_all_staff()

@router.post("/", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
async def create_staff(staff: StaffCreate):
    return StaffLogic.add_staff(staff)
@router.get("/{staff_id}", response_model=StaffResponse)
async def get_staff_by_id(staff_id: str):
    return StaffLogic.get_staff_by_id(staff_id)

@router.put("/{staff_id}", response_model=StaffResponse)
async def update_staff(staff_id: str, staff: StaffCreate):
    return StaffLogic.update_staff(staff_id, staff)

@router.delete("/{staff_id}")
async def delete_staff(staff_id: str):
    return StaffLogic.remove_staff(staff_id)