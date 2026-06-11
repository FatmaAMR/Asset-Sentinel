from fastapi import APIRouter, HTTPException
from db.connection import get_collection

router = APIRouter()

@router.get("/machines/{machine_id}/sensor-window")
async def get_sensor_window(machine_id: str):
    """
    Returns the raw s_4 and s_9 arrays for a machine from its latest MongoDB document.
    Used by the VibrationStream component to animate live sensor data.
    """
    try:
        collection = get_collection()
        doc = collection.find_one(
            {"machine_id": machine_id},
            {"_id": 0, "raw": 1}
        )
        if not doc:
            raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")

        raw_inner = doc.get("raw", {}).get("raw", {})

        def safe_list(arr):
            result = []
            for v in arr:
                if isinstance(v, dict):
                    try:
                        result.append(float(v.get("$numberDouble", 0)))
                    except (TypeError, ValueError):
                        result.append(0.0)
                else:
                    try:
                        result.append(float(v))
                    except (TypeError, ValueError):
                        result.append(0.0)
            return result

        return {
            "machine_id": machine_id,
            "s4": safe_list(raw_inner.get("s_4", [])),
            "s9": safe_list(raw_inner.get("s_9", [])),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))