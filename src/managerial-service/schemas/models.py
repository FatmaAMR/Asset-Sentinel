from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum

# ==========================================
# 1. Enums
# ==========================================
class RoleEnum(str, Enum):
    admin = "Admin"
    technician = "Technician"
    manager = "Manager"

class AssetStatusEnum(str, Enum):
    active = "Active"
    maintenance = "Under Maintenance"
    decommissioned = "Decommissioned"

# ==========================================
# 2. Staff Schemas
# ==========================================
class StaffCreate(BaseModel):
    full_name: str
    email: str
    role: str
    password: str

class StaffResponse(BaseModel):
    staff_id: str
    full_name: str
    email: str
    role: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# ==========================================
# 3. Factory Assets Schemas
# ==========================================
class AssetBase(BaseModel):
    asset_id: str = Field(..., example="MOTOR-001")
    machine_type: str = Field(..., example="FD001")
    location_floor: int
    location_section: str
    specifications: Optional[Dict[str, Any]] = {}
    status: AssetStatusEnum = AssetStatusEnum.active

    class Config:
        from_attributes = True  # مهم عشان يشتغل مع SQLAlchemy

class AssetCreate(AssetBase):
    pass

class AssetResponse(AssetBase):
    pass

# ==========================================
# 4. Threshold Rules Schemas
# ==========================================
class ThresholdRuleBase(BaseModel):
    machine_type: str = Field(..., example="FD001")
    warning_limit: float
    critical_limit: float

    class Config:
        from_attributes = True

class ThresholdRuleCreate(ThresholdRuleBase):
    updated_by_staff_id: str

class ThresholdRuleResponse(ThresholdRuleBase):
    rule_id: str
    updated_by_staff_id: str