from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List
from enum import Enum

# ==========================================
# 1. Enums (الثوابت)
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
# 2. Staff Schemas (جدول الموظفين/المهندسين)
# ==========================================
class StaffBase(BaseModel):
    full_name: str
    role: RoleEnum
    email: EmailStr

class StaffCreate(StaffBase):
    password: str

class StaffResponse(StaffBase):
    staff_id: str
    created_at: str

# ==========================================
# 3. Factory Assets Schemas (جدول المكن)
# ==========================================
class AssetBase(BaseModel):
    asset_id: str = Field(..., example="MOTOR-001")
    machine_type: str = Field(..., example="FD001")
    location_floor: int
    location_section: str
    specifications: Optional[Dict[str, Any]] = {}
    status: AssetStatusEnum = AssetStatusEnum.active

class AssetCreate(AssetBase):
    pass

class AssetResponse(AssetBase):
    pass

# ==========================================
# 4. Threshold Rules Schemas (قواعد التنبيهات)
# ==========================================
class ThresholdRuleBase(BaseModel):
    machine_type: str = Field(..., example="FD001")
    warning_limit: float = Field(..., description="RUL limit for warning (e.g., 30)")
    critical_limit: float = Field(..., description="RUL limit for critical (e.g., 15)")

class ThresholdRuleCreate(ThresholdRuleBase):
    updated_by_staff_id: str

class ThresholdRuleResponse(ThresholdRuleBase):
    rule_id: str
    updated_by_staff_id: str