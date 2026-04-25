from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router as reports_router

app = FastAPI(title="Sentinel-AI Reporting Service", version="1.0")

# إعدادات الـ CORS عشان الداشبورد تعرف تكلم السيرفر من غير ما المتصفح يعمل Block
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # في الـ Production هنغير النجمة دي ونحط لينك الفرونت إند الحقيقي
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# بنربط الـ Routes اللي عملناها بالتطبيق الأساسي
app.include_router(reports_router, prefix="/api/v1/reports", tags=["Reports"])

@app.get("/")
async def root():
    return {"message": "Reporting Service is up and running smoothly! 🚀"}