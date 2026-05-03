from fastapi import APIRouter, status
from typing import List
from schemas.models import ThresholdRuleCreate, ThresholdRuleResponse
from services.logic import ThresholdLogic

router = APIRouter(prefix="/thresholds", tags=["Threshold Rules"])

@router.get("/", response_model=List[ThresholdRuleResponse])
async def get_all_thresholds():
    return ThresholdLogic.list_all_rules()

@router.post("/", response_model=ThresholdRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_threshold(rule: ThresholdRuleCreate):
    return ThresholdLogic.add_rule(rule)

@router.get("/{rule_id}", response_model=ThresholdRuleResponse)
async def get_threshold_by_id(rule_id: str):
    return ThresholdLogic.get_rule_by_id(rule_id)

@router.put("/{rule_id}", response_model=ThresholdRuleResponse)
async def update_threshold(rule_id: str, rule: ThresholdRuleCreate):
    return ThresholdLogic.update_rule(rule_id, rule)

@router.delete("/{rule_id}")
async def delete_threshold(rule_id: str):
    return ThresholdLogic.delete_rule(rule_id)