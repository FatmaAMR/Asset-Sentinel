from fastapi import APIRouter, status, Depends
from sqlalchemy.orm import Session # إضافة جديدة
from typing import List
from schemas.models import AssetCreate, AssetResponse
from services.logic import AssetLogic
from services.security import get_current_user, require_role
from db.connection import get_db
from db.models import DBStaff
from services.security import verify_password, create_access_token
from services.security import get_current_user, require_role

router = APIRouter(prefix="/assets", tags=["Assets Management"])

# Admin و Manager بس يضيفوا assets
@router.post("/", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    asset: AssetCreate,
    current_user: dict = Depends(require_role("Admin", "Manager")),
    db: Session = Depends(get_db) # فتحنا اتصال الداتا بيز
):
    return AssetLogic.add_new_asset(asset, db) # باصينا الـ db للوجيك

# أي logged-in user يشوف كل الـ assets
@router.get("/", response_model=List[AssetResponse])
async def get_all_assets(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db) # فتحنا اتصال الداتا بيز
):
    return AssetLogic.list_all_assets(db) # باصينا الـ db للوجيك

# أي logged-in user يشوف asset معين
@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset_by_id(
    asset_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db) # فتحنا اتصال الداتا بيز
):
    return AssetLogic.get_asset(asset_id, db) # باصينا الـ db للوجيك

# Admin و Manager بس يعدلوا
@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: str,
    asset: AssetCreate,
    current_user: dict = Depends(require_role("Admin", "Manager")),
    db: Session = Depends(get_db) # فتحنا اتصال الداتا بيز
):
    return AssetLogic.update_existing_asset(asset_id, asset, db) # باصينا الـ db للوجيك

# Admin بس يمسح
@router.delete("/{asset_id}")
async def delete_asset(
    asset_id: str,
    current_user: dict = Depends(require_role("Admin")),
    db: Session = Depends(get_db) # فتحنا اتصال الداتا بيز
):
    return AssetLogic.remove_asset(asset_id, db) # باصينا الـ db للوجيك