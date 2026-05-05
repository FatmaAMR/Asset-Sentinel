from fastapi import FastAPI
from database import engine, Base
import db_models

# لازم يكون أول حاجة قبل أي حاجة تانية
Base.metadata.create_all(bind=engine)

from api.asset_routes import router as asset_router
from api.staff_routes import router as staff_router
from api.threshold_routes import router as threshold_router
from api import auth_routes

app = FastAPI(title="Managerial Service - Asset Sentinel")

app.include_router(asset_router, prefix="/api/v1/managerial")
app.include_router(staff_router, prefix="/api/v1/managerial")
app.include_router(threshold_router, prefix="/api/v1/managerial")
app.include_router(auth_routes.router, prefix="/api/v1/managerial")

@app.get("/")
async def root():
    return {"message": "Managerial Service is running"}