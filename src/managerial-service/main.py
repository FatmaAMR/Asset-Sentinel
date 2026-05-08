from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.asset_routes import router as asset_router
from api.staff_routes import router as staff_router
from api.threshold_routes import router as threshold_router
from api import auth_routes
from db.connection import engine, Base
from db import models # بدل import db_models

# تكريت الجداول في الداتا بيز أول ما السيرفر يقوم
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Managerial Service - Asset Sentinel")

# إعدادات الـ CORS عشان تسمح للفرونت إند يكلم السيرفر
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ربط الـ Routers المختلفة
app.include_router(asset_router, prefix="/api/v1/managerial")
app.include_router(staff_router, prefix="/api/v1/managerial")
app.include_router(threshold_router, prefix="/api/v1/managerial")
app.include_router(auth_routes.router, prefix="/api/v1/managerial")

@app.get("/")
async def root():
    return {"message": "Managerial Service is running"}