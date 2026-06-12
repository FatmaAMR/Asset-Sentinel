from fastapi import HTTPException, status
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorCollection
import uuid

from schemas.models import AssetCreate, StaffCreate, ThresholdRuleCreate
from .security import get_password_hash, verify_password
from db.models import STAFF_COLLECTION, ASSET_COLLECTION, THRESHOLD_COLLECTION
from db.connection import get_collection


class AssetLogic:
    @staticmethod
    async def add_new_asset(asset: AssetCreate):
        col = get_collection(ASSET_COLLECTION)
        if await col.find_one({"asset_id": asset.asset_id}):
            raise HTTPException(400, "Asset ID already exists")
        doc = asset.dict()
        doc["status"] = asset.status.value if hasattr(asset.status, "value") else asset.status
        await col.insert_one(doc)
        return doc

    @staticmethod
    async def list_all_assets():
        col = get_collection(ASSET_COLLECTION)
        return [a async for a in col.find({}, {"_id": 0})]

    @staticmethod
    async def get_asset(asset_id: str):
        col = get_collection(ASSET_COLLECTION)
        asset = await col.find_one({"asset_id": asset_id}, {"_id": 0})
        if not asset:
            raise HTTPException(404, "Asset not found")
        return asset

    @staticmethod
    async def update_existing_asset(asset_id: str, asset_data: AssetCreate):
        col = get_collection(ASSET_COLLECTION)
        doc = asset_data.dict()
        doc["status"] = asset_data.status.value if hasattr(asset_data.status, "value") else asset_data.status
        result = await col.find_one_and_replace(
            {"asset_id": asset_id}, doc, return_document=True
        )
        if not result:
            raise HTTPException(404, "Asset not found")
        result.pop("_id", None)
        return result

    @staticmethod
    async def remove_asset(asset_id: str):
        col = get_collection(ASSET_COLLECTION)
        result = await col.delete_one({"asset_id": asset_id})
        if result.deleted_count == 0:
            raise HTTPException(404, "Asset not found")
        return {"message": f"Asset {asset_id} deleted successfully"}


class StaffLogic:
    @staticmethod
    async def add_staff(staff: StaffCreate):
        col = get_collection(STAFF_COLLECTION)
        if await col.find_one({"email": staff.email}):
            raise HTTPException(400, "Email already registered")
        new_id = f"EMP-{uuid.uuid4().hex[:4].upper()}"
        doc = {
            "staff_id":   new_id,
            "full_name":  staff.full_name,
            "role":       staff.role,
            "email":      staff.email,
            "password":   get_password_hash(staff.password),
            "created_at": datetime.utcnow().strftime("%Y-%m-%d"),
        }
        await col.insert_one(doc)
        doc.pop("_id", None)
        return doc

    @staticmethod
    async def authenticate_user(email: str, password: str):
        col = get_collection(STAFF_COLLECTION)
        user = await col.find_one({"email": email}, {"_id": 0})
        if not user or not verify_password(password, user["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    @staticmethod
    async def list_all_staff():
        col = get_collection(STAFF_COLLECTION)
        return [s async for s in col.find({}, {"_id": 0, "password": 0})]

    @staticmethod
    async def get_staff_by_id(staff_id: str):
        col = get_collection(STAFF_COLLECTION)
        user = await col.find_one({"staff_id": staff_id}, {"_id": 0, "password": 0})
        if not user:
            raise HTTPException(404, "Staff not found")
        return user

    @staticmethod
    async def update_staff(staff_id: str, staff_data: StaffCreate):
        col = get_collection(STAFF_COLLECTION)
        update = {
            "full_name": staff_data.full_name,
            "role":      staff_data.role,
            "email":     staff_data.email,
            "password":  get_password_hash(staff_data.password),
        }
        result = await col.find_one_and_update(
            {"staff_id": staff_id},
            {"$set": update},
            return_document=True,
        )
        if not result:
            raise HTTPException(404, "Staff not found")
        result.pop("_id", None)
        result.pop("password", None)
        return result

    @staticmethod
    async def remove_staff(staff_id: str):
        col = get_collection(STAFF_COLLECTION)
        result = await col.delete_one({"staff_id": staff_id})
        if result.deleted_count == 0:
            raise HTTPException(404, "Staff not found")
        return {"message": f"Staff {staff_id} deleted successfully"}

    @staticmethod
    async def change_staff_password(email: str, old_pw: str, new_pw: str):
        col = get_collection(STAFF_COLLECTION)
        user = await col.find_one({"email": email})
        if not user:
            raise HTTPException(404, "Staff not found")
        if not verify_password(old_pw, user["password"]):
            raise HTTPException(400, "Incorrect old password")
        await col.update_one({"email": email}, {"$set": {"password": get_password_hash(new_pw)}})
        return {"message": "Password updated successfully"}


class ThresholdLogic:
    @staticmethod
    async def add_rule(rule: ThresholdRuleCreate):
        col = get_collection(THRESHOLD_COLLECTION)
        rule_id = f"THR-{uuid.uuid4().hex[:4].upper()}"
        doc = {
            "rule_id":              rule_id,
            "machine_type":         rule.machine_type,
            "warning_limit":        rule.warning_limit,
            "critical_limit":       rule.critical_limit,
            "updated_by_staff_id":  rule.updated_by_staff_id,
        }
        await col.insert_one(doc)
        doc.pop("_id", None)
        return doc

    @staticmethod
    async def list_all_rules():
        col = get_collection(THRESHOLD_COLLECTION)
        return [r async for r in col.find({}, {"_id": 0})]

    @staticmethod
    async def get_rule_by_id(rule_id: str):
        col = get_collection(THRESHOLD_COLLECTION)
        rule = await col.find_one({"rule_id": rule_id}, {"_id": 0})
        if not rule:
            raise HTTPException(404, "Threshold rule not found")
        return rule

    @staticmethod
    async def update_rule(rule_id: str, rule_data: ThresholdRuleCreate):
        col = get_collection(THRESHOLD_COLLECTION)
        update = {
            "machine_type":        rule_data.machine_type,
            "warning_limit":       rule_data.warning_limit,
            "critical_limit":      rule_data.critical_limit,
            "updated_by_staff_id": rule_data.updated_by_staff_id,
        }
        result = await col.find_one_and_update(
            {"rule_id": rule_id}, {"$set": update}, return_document=True
        )
        if not result:
            raise HTTPException(404, "Threshold rule not found")
        result.pop("_id", None)
        return result

    @staticmethod
    async def delete_rule(rule_id: str):
        col = get_collection(THRESHOLD_COLLECTION)
        result = await col.delete_one({"rule_id": rule_id})
        if result.deleted_count == 0:
            raise HTTPException(404, "Threshold rule not found")
        return {"message": f"Threshold rule {rule_id} deleted successfully"}