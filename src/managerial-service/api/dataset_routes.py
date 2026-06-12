from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pathlib import Path
from datetime import datetime
from services.security import require_role
from db.connection import get_collection
from db.models import DATASET_COLLECTION
import shutil
import uuid

RAW_DIR = Path(__file__).resolve().parent.parent.parent / "raw"

router = APIRouter(prefix="/datasets", tags=["Dataset Upload"])

@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_role("Admin")),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Only CSV files are supported")

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_name = f"{timestamp}_{file.filename}"
    save_path = RAW_DIR / safe_name

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    col = get_collection(DATASET_COLLECTION)
    record = {
        "dataset_id":    f"DS-{uuid.uuid4().hex[:6].upper()}",
        "filename":      safe_name,
        "original_name": file.filename,
        "uploaded_by":   current_user["email"],
        "uploaded_at":   datetime.utcnow().isoformat(),
        "path":          str(save_path),
    }
    await col.insert_one(record)
    record.pop("_id", None)

    return {"message": "Dataset uploaded successfully", "dataset": record}

@router.delete("/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    current_user: dict = Depends(require_role("Admin")),
):
    col = get_collection(DATASET_COLLECTION)
    record = await col.find_one({"dataset_id": dataset_id})
    if not record:
        raise HTTPException(404, "Dataset not found")
    
    # delete file from disk if it exists
    file_path = Path(record["path"])
    if file_path.exists():
        file_path.unlink()
    
    await col.delete_one({"dataset_id": dataset_id})
    return {"message": f"Dataset {dataset_id} deleted successfully"}

@router.get("/")
async def list_datasets(current_user: dict = Depends(require_role("Admin"))):
    col = get_collection(DATASET_COLLECTION)
    return [d async for d in col.find({}, {"_id": 0})]