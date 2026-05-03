from fastapi import HTTPException, status # تأكد من وجود status هنا[cite: 5]
from schemas.models import AssetCreate, AssetStatusEnum, StaffCreate, ThresholdRuleCreate
from services.security import verify_password, get_password_hash
# ==========================================
# 1. Assets In-Memory DB & Logic
# ==========================================
mock_db_assets = {
    "MOTOR-001": {
        "asset_id": "MOTOR-001", 
        "machine_type": "FD001", 
        "location_floor": 1,
        "location_section": "Section A", 
        "specifications": {"max_rpm": 1500},
        "status": AssetStatusEnum.active
    }
}

class AssetLogic:
    @staticmethod
    def add_new_asset(asset: AssetCreate):
        if asset.asset_id in mock_db_assets:
            raise HTTPException(status_code=400, detail="Asset ID already exists")
        mock_db_assets[asset.asset_id] = asset.model_dump()
        return mock_db_assets[asset.asset_id]

    @staticmethod
    def list_all_assets():
        return list(mock_db_assets.values())

    @staticmethod
    def get_asset(asset_id: str):
        if asset_id not in mock_db_assets:
            raise HTTPException(status_code=404, detail="Asset not found")
        return mock_db_assets[asset_id]

    @staticmethod
    def update_existing_asset(asset_id: str, asset: AssetCreate):
        if asset_id not in mock_db_assets:
            raise HTTPException(status_code=404, detail="Asset not found")
        mock_db_assets[asset_id] = asset.model_dump()
        return mock_db_assets[asset_id]

    @staticmethod
    def remove_asset(asset_id: str):
        if asset_id not in mock_db_assets:
            raise HTTPException(status_code=404, detail="Asset not found")
        del mock_db_assets[asset_id]
        return {"message": f"Asset {asset_id} deleted successfully"}

# ==========================================
# 2. Staff In-Memory DB & Logic
# ==========================================
mock_db_staff = {
    "EMP-001": {
        "staff_id": "EMP-001", 
        "full_name": "Ezz Ahmed", 
        "role": "Admin", 
        "email": "ezz@factory.com", 
        "password": get_password_hash("123456"),
        "created_at": "2026-05-03"
    }
}


class StaffLogic:
    @staticmethod
    def add_staff(staff: StaffCreate):
        new_id = f"EMP-{len(mock_db_staff) + 1:03d}"
        hashed_pw = get_password_hash(staff.password)
        new_staff = {
            "staff_id": new_id, "full_name": staff.full_name,
            "role": staff.role, "email": staff.email,
            "password": hashed_pw, "created_at": "2026-05-03"
        }
        mock_db_staff[new_id] = new_staff
        return new_staff

    @staticmethod
    def change_staff_password(email: str, old_pw: str, new_pw: str):
        user_id, user_data = None, None
        for uid, staff in mock_db_staff.items():
            if staff["email"] == email:
                user_id, user_data = uid, staff
                break
        
        if not user_data:
            raise HTTPException(status_code=404, detail="Staff not found")

        if not verify_password(old_pw, user_data["password"]):
            raise HTTPException(status_code=400, detail="Incorrect old password")

        mock_db_staff[user_id]["password"] = get_password_hash(new_pw)
        return {"message": "Password updated successfully"}

    @staticmethod
    def authenticate_user(email: str, password: str):
        user = None
        for staff in mock_db_staff.values():
            if staff["email"] == email:
                user = staff
                break

        if not user or not verify_password(password, user["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    @staticmethod
    def list_all_staff():
        return list(mock_db_staff.values())
    
    @staticmethod
    def get_staff_by_id(staff_id: str):
        if staff_id not in mock_db_staff:
            raise HTTPException(status_code=404, detail="Staff not found")
        return mock_db_staff[staff_id]

    @staticmethod
    def update_staff(staff_id: str, staff: StaffCreate):
        if staff_id not in mock_db_staff:
            raise HTTPException(status_code=404, detail="Staff not found")
        
        updated_staff = {
            "staff_id": staff_id, "full_name": staff.full_name,
            "role": staff.role, "email": staff.email,
            "password": get_password_hash(staff.password),
            "created_at": mock_db_staff[staff_id]["created_at"]
        }
        mock_db_staff[staff_id] = updated_staff
        return updated_staff

    @staticmethod
    def remove_staff(staff_id: str):
        if staff_id not in mock_db_staff:
            raise HTTPException(status_code=404, detail="Staff not found")
        del mock_db_staff[staff_id]
        return {"message": f"Staff {staff_id} deleted successfully"}
    
# ==========================================
# 3. Threshold Rules In-Memory DB & Logic
# ==========================================
mock_db_thresholds = {
    "THR-001": {
        "rule_id": "THR-001",
        "machine_type": "FD001",
        "warning_limit": 75.0,
        "critical_limit": 90.0,
        "updated_by_staff_id": "EMP-001"
    }
}

class ThresholdLogic:
    @staticmethod
    def add_rule(rule: ThresholdRuleCreate):
        rule_id = f"THR-{len(mock_db_thresholds) + 1:03d}"
        new_rule = {
            "rule_id": rule_id,
            "machine_type": rule.machine_type,
            "warning_limit": rule.warning_limit,
            "critical_limit": rule.critical_limit,
            "updated_by_staff_id": rule.updated_by_staff_id
        }
        mock_db_thresholds[rule_id] = new_rule
        return new_rule

    @staticmethod
    def list_all_rules():
        return list(mock_db_thresholds.values())

    @staticmethod
    def get_rule_by_id(rule_id: str):
        if rule_id not in mock_db_thresholds:
            raise HTTPException(status_code=404, detail="Threshold rule not found")
        return mock_db_thresholds[rule_id]

    @staticmethod
    def update_rule(rule_id: str, rule: ThresholdRuleCreate):
        if rule_id not in mock_db_thresholds:
            raise HTTPException(status_code=404, detail="Threshold rule not found")
        
        updated_rule = {
            "rule_id": rule_id,
            "machine_type": rule.machine_type,
            "warning_limit": rule.warning_limit,
            "critical_limit": rule.critical_limit,
            "updated_by_staff_id": rule.updated_by_staff_id
        }
        mock_db_thresholds[rule_id] = updated_rule
        return updated_rule

    @staticmethod
    def delete_rule(rule_id: str):
        if rule_id not in mock_db_thresholds:
            raise HTTPException(status_code=404, detail="Threshold rule not found")
        del mock_db_thresholds[rule_id]
        return {"message": f"Threshold rule {rule_id} deleted successfully"}