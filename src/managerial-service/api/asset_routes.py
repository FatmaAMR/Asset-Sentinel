from fastapi import APIRouter, status, Depends
from typing import List
from schemas.models import AssetCreate, AssetResponse
from services.logic import AssetLogic
from services.security import get_current_user, require_role

router = APIRouter(prefix="/assets", tags=["Assets Management"])

@router.post("/", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    asset: AssetCreate,
    current_user: dict = Depends(require_role("Admin", "Manager")),
):
    return await AssetLogic.add_new_asset(asset)

@router.get("/", response_model=List[AssetResponse])
async def get_all_assets(current_user: dict = Depends(get_current_user)):
    return await AssetLogic.list_all_assets()

@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset_by_id(
    asset_id: str,
    current_user: dict = Depends(get_current_user),
):
    return await AssetLogic.get_asset(asset_id)


@router.put("/{asset_id}", response_model=AssetResponse)

async def update_asset(
    asset_id: str,
    asset: AssetCreate,
    current_user: dict = Depends(require_role("Admin", "Manager")),

):
    
    return await AssetLogic.update_existing_asset(asset_id, asset)


@router.delete("/{asset_id}")

async def delete_asset(
    asset_id: str,
    current_user: dict = Depends(require_role("Admin")),

):
    return await AssetLogic.remove_asset(asset_id)