from fastapi import APIRouter, status
from typing import List
from schemas.models import AssetCreate, AssetResponse
from services.logic import AssetLogic

router = APIRouter(prefix="/assets", tags=["Assets Management"])

@router.post("/", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(asset: AssetCreate):
    return AssetLogic.add_new_asset(asset)

@router.get("/", response_model=List[AssetResponse])
async def get_all_assets():
    return AssetLogic.list_all_assets()

@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset_by_id(asset_id: str):
    return AssetLogic.get_asset(asset_id)

@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(asset_id: str, asset: AssetCreate):
    return AssetLogic.update_existing_asset(asset_id, asset)

@router.delete("/{asset_id}")
async def delete_asset(asset_id: str):
    return AssetLogic.remove_asset(asset_id)