from fastapi import FastAPI
from api.asset_routes import router as asset_router
from api.staff_routes import router as staff_router
from api.threshold_routes import router as threshold_router # السطر ده جديد
from api import auth_routes

app = FastAPI(title="Managerial Service - Asset Sentinel")

app.include_router(asset_router, prefix="/api/v1/managerial")
app.include_router(staff_router, prefix="/api/v1/managerial")
app.include_router(threshold_router, prefix="/api/v1/managerial")
app.include_router(auth_routes.router, prefix="/api/v1/managerial")
@app.get("/")
async def root():
    return {"message": "Managerial Service is running"}