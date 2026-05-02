from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from schemas.models import FactoryReport
from services.analytics import process_factory_data
from db.connection import get_mock_influx_data
from schemas.models import MachineHistoryResponse, MachineDetailsResponse, Alert
from services.analytics import get_machine_history, get_machine_details, get_active_alerts
from typing import List

router = APIRouter()

@router.get("/factory-summary", response_model=FactoryReport)
async def get_factory_summary(
    status: Optional[str] = Query(None, description="فلترة حسب الحالة: Critical, Warning, Normal"),
    db_source = Depends(get_mock_influx_data) 
):
    try:
        # شيلنا الـ await من هنا لأن FastAPI عملها بدالنا في الـ Depends
        raw_data = db_source 
        
        if not raw_data:
            raise HTTPException(status_code=404, detail="No sensor data found")

        # هنا بنسيب الـ await زي ما هي لأننا بننادي على الـ function بنفسنا
        report = await process_factory_data(raw_data, status_filter=status)
        return report

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    @router.get("/machines/{machine_id}/history", response_model=MachineHistoryResponse)

    async def get_history(
    machine_id: str, 
    limit: int = Query(50, description="عدد القراءات المطلوبة"), 
    db_source = Depends(get_mock_influx_data)
):
     data = await get_machine_history(db_source, machine_id, limit)
    if not data:
        raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
    return data

@router.get("/machines/{machine_id}/history", response_model=MachineHistoryResponse)
async def get_history(
    machine_id: str, 
    limit: int = Query(50, description="عدد القراءات المطلوبة"), 
    db_source = Depends(get_mock_influx_data)
):
    data = await get_machine_history(db_source, machine_id, limit)
    if not data:
        raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
    return data


@router.get("/machines/{machine_id}", response_model=MachineDetailsResponse)
async def get_details(machine_id: str, db_source = Depends(get_mock_influx_data)):
    data = await get_machine_details(db_source, machine_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
    return data


@router.get("/alerts", response_model=List[Alert])
async def get_alerts(
    status: Optional[str] = Query(None, description="فلترة حسب الخطورة: Critical, Warning"), 
    db_source = Depends(get_mock_influx_data)
):
    alerts = await get_active_alerts(db_source, status_filter=status)
    return alerts