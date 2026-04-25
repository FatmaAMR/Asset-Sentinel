from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from schemas.models import FactoryReport
from services.analytics import process_factory_data
from db.connection import get_mock_influx_data

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