from fastapi import APIRouter, status, Depends
from sqlalchemy.orm import Session # إضافة جديدة
from typing import List
from schemas.models import ThresholdRuleCreate, ThresholdRuleResponse
from services.logic import ThresholdLogic
from db.connection import get_db
from db.models import DBStaff
from services.security import verify_password, create_access_token
from services.security import get_current_user, require_role

router = APIRouter(prefix="/thresholds", tags=["Threshold Rules"])

# أي logged-in user يشوف الـ thresholds
@router.get("/", response_model=List[ThresholdRuleResponse])
async def get_all_thresholds(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db) # فتح اتصال الداتا بيز
):
    return ThresholdLogic.list_all_rules(db) # باصينا الـ db

# Admin و Manager بس يضيفوا rules
@router.post("/", response_model=ThresholdRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_threshold(
    rule: ThresholdRuleCreate,
    current_user: dict = Depends(require_role("Admin", "Manager")),
    db: Session = Depends(get_db) # فتح اتصال الداتا بيز
):
    return ThresholdLogic.add_rule(rule, db) # باصينا الـ db

# أي logged-in user يشوف rule معين
@router.get("/{rule_id}", response_model=ThresholdRuleResponse)
async def get_threshold_by_id(
    rule_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db) # فتح اتصال الداتا بيز
):
    return ThresholdLogic.get_rule_by_id(rule_id, db) # باصينا الـ db

# Admin و Manager بس يعدلوا
@router.put("/{rule_id}", response_model=ThresholdRuleResponse)
async def update_threshold(
    rule_id: str,
    rule: ThresholdRuleCreate,
    current_user: dict = Depends(require_role("Admin", "Manager")),
    db: Session = Depends(get_db) # فتح اتصال الداتا بيز
):
    return ThresholdLogic.update_rule(rule_id, rule, db) # باصينا الـ db

# Admin بس يمسح
@router.delete("/{rule_id}")
async def delete_threshold(
    rule_id: str,
    current_user: dict = Depends(require_role("Admin")),
    db: Session = Depends(get_db) # فتح اتصال الداتا بيز
):
    return ThresholdLogic.delete_rule(rule_id, db) # باصينا الـ db