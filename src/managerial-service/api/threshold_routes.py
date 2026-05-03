from fastapi import APIRouter, status, Depends
from typing import List
from schemas.models import ThresholdRuleCreate, ThresholdRuleResponse
from services.logic import ThresholdLogic
from services.security import get_current_user, require_role

router = APIRouter(prefix="/thresholds", tags=["Threshold Rules"])

# أي logged-in user يشوف الـ thresholds
@router.get("/", response_model=List[ThresholdRuleResponse])
async def get_all_thresholds(
    current_user: dict = Depends(get_current_user)
):
    return ThresholdLogic.list_all_rules()

# Admin و Manager بس يضيفوا rules
@router.post("/", response_model=ThresholdRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_threshold(
    rule: ThresholdRuleCreate,
    current_user: dict = Depends(require_role("Admin", "Manager"))
):
    return ThresholdLogic.add_rule(rule)

# أي logged-in user يشوف rule معين
@router.get("/{rule_id}", response_model=ThresholdRuleResponse)
async def get_threshold_by_id(
    rule_id: str,
    current_user: dict = Depends(get_current_user)
):
    return ThresholdLogic.get_rule_by_id(rule_id)

# Admin و Manager بس يعدلوا
@router.put("/{rule_id}", response_model=ThresholdRuleResponse)
async def update_threshold(
    rule_id: str,
    rule: ThresholdRuleCreate,
    current_user: dict = Depends(require_role("Admin", "Manager"))
):
    return ThresholdLogic.update_rule(rule_id, rule)

# Admin بس يمسح
@router.delete("/{rule_id}")
async def delete_threshold(
    rule_id: str,
    current_user: dict = Depends(require_role("Admin"))
):
    return ThresholdLogic.delete_rule(rule_id)