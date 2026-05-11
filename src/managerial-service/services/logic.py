from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

# 1. استدعاء السكيما (Pydantic Models)
from schemas.models import AssetCreate, AssetStatusEnum, StaffCreate, ThresholdRuleCreate

# 2. استدعاء التشفير (بما إن logic و security في نفس فولدر services بنستخدم الـ dot)
from .security import verify_password, get_password_hash

# 3. استدعاء جداول الداتا بيز من المسار الجديد
from db.models import DBAsset, DBStaff, DBThreshold
# ==========================================
# 1. Assets Logic
# ==========================================
class AssetLogic:
    @staticmethod
    def add_new_asset(asset: AssetCreate, db: Session):
        existing_asset = db.query(DBAsset).filter(DBAsset.asset_id == asset.asset_id).first()
        if existing_asset:
            raise HTTPException(status_code=400, detail="Asset ID already exists")
        
        new_asset = DBAsset(
            asset_id=asset.asset_id,
            machine_type=asset.machine_type,
            location_floor=asset.location_floor,
            location_section=asset.location_section,
            specifications=asset.specifications,
            status=asset.status.value if hasattr(asset.status, 'value') else asset.status
        )
        db.add(new_asset)
        db.commit()
        db.refresh(new_asset)
        return new_asset

    @staticmethod
    def list_all_assets(db: Session):
        return db.query(DBAsset).all()

    @staticmethod
    def get_asset(asset_id: str, db: Session):
        asset = db.query(DBAsset).filter(DBAsset.asset_id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        return asset

    @staticmethod
    def update_existing_asset(asset_id: str, asset_data: AssetCreate, db: Session):
        asset = db.query(DBAsset).filter(DBAsset.asset_id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        asset.machine_type = asset_data.machine_type
        asset.location_floor = asset_data.location_floor
        asset.location_section = asset_data.location_section
        asset.specifications = asset_data.specifications
        asset.status = asset_data.status.value if hasattr(asset_data.status, 'value') else asset_data.status
        
        db.commit()
        db.refresh(asset)
        return asset

    @staticmethod
    def remove_asset(asset_id: str, db: Session):
        asset = db.query(DBAsset).filter(DBAsset.asset_id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        db.delete(asset)
        db.commit()
        return {"message": f"Asset {asset_id} deleted successfully"}

# ==========================================
# 2. Staff Logic
# ==========================================
class StaffLogic:
    @staticmethod
    def add_staff(staff: StaffCreate, db: Session):
        existing_user = db.query(DBStaff).filter(DBStaff.email == staff.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # بنستخدم UUID عشان نضمن إن الـ ID مش هيتكرر حتى لو مسحنا موظفين
        new_id = f"EMP-{uuid.uuid4().hex[:4].upper()}"
        
        new_staff = DBStaff(
            staff_id=new_id,
            full_name=staff.full_name,
            role=staff.role,
            email=staff.email,
            password=get_password_hash(staff.password),
            created_at=datetime.utcnow().strftime("%Y-%m-%d")
        )
        db.add(new_staff)
        db.commit()
        db.refresh(new_staff)
        return new_staff

    @staticmethod
    def change_staff_password(email: str, old_pw: str, new_pw: str, db: Session):
        user = db.query(DBStaff).filter(DBStaff.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Staff not found")

        if not verify_password(old_pw, user.password):
            raise HTTPException(status_code=400, detail="Incorrect old password")

        user.password = get_password_hash(new_pw)
        db.commit()
        return {"message": "Password updated successfully"}

    @staticmethod
    def authenticate_user(email: str, password: str, db: Session):
        user = db.query(DBStaff).filter(DBStaff.email == email).first()
        if not user or not verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    @staticmethod
    def list_all_staff(db: Session):
        return db.query(DBStaff).all()

    @staticmethod
    def get_staff_by_id(staff_id: str, db: Session):
        user = db.query(DBStaff).filter(DBStaff.staff_id == staff_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Staff not found")
        return user

    @staticmethod
    def update_staff(staff_id: str, staff_data: StaffCreate, db: Session):
        user = db.query(DBStaff).filter(DBStaff.staff_id == staff_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Staff not found")
        
        user.full_name = staff_data.full_name
        user.role = staff_data.role
        user.email = staff_data.email
        user.password = get_password_hash(staff_data.password)
        # created_at بيفضل زي ما هو مش بنعدله
        
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def remove_staff(staff_id: str, db: Session):
        user = db.query(DBStaff).filter(DBStaff.staff_id == staff_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Staff not found")
        
        db.delete(user)
        db.commit()
        return {"message": f"Staff {staff_id} deleted successfully"}

# ==========================================
# 3. Threshold Rules Logic
# ==========================================
class ThresholdLogic:
    @staticmethod
    def add_rule(rule: ThresholdRuleCreate, db: Session):
        rule_id = f"THR-{uuid.uuid4().hex[:4].upper()}"
        new_rule = DBThreshold(
            rule_id=rule_id,
            machine_type=rule.machine_type,
            warning_limit=rule.warning_limit,
            critical_limit=rule.critical_limit,
            updated_by_staff_id=rule.updated_by_staff_id
        )
        db.add(new_rule)
        db.commit()
        db.refresh(new_rule)
        return new_rule

    @staticmethod
    def list_all_rules(db: Session):
        return db.query(DBThreshold).all()

    @staticmethod
    def get_rule_by_id(rule_id: str, db: Session):
        rule = db.query(DBThreshold).filter(DBThreshold.rule_id == rule_id).first()
        if not rule:
            raise HTTPException(status_code=404, detail="Threshold rule not found")
        return rule

    @staticmethod
    def update_rule(rule_id: str, rule_data: ThresholdRuleCreate, db: Session):
        rule = db.query(DBThreshold).filter(DBThreshold.rule_id == rule_id).first()
        if not rule:
            raise HTTPException(status_code=404, detail="Threshold rule not found")
        
        rule.machine_type = rule_data.machine_type
        rule.warning_limit = rule_data.warning_limit
        rule.critical_limit = rule_data.critical_limit
        rule.updated_by_staff_id = rule_data.updated_by_staff_id
        
        db.commit()
        db.refresh(rule)
        return rule

    @staticmethod
    def delete_rule(rule_id: str, db: Session):
        rule = db.query(DBThreshold).filter(DBThreshold.rule_id == rule_id).first()
        if not rule:
            raise HTTPException(status_code=404, detail="Threshold rule not found")
        
        db.delete(rule)
        db.commit()
        return {"message": f"Threshold rule {rule_id} deleted successfully"}