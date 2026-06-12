from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.asset_routes     import router as asset_router
from api.staff_routes     import router as staff_router
from api.threshold_routes import router as threshold_router
from api.dataset_routes   import router as dataset_router
from api                  import auth_routes

app = FastAPI(title="Managerial Service - Asset Sentinel")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(asset_router,     prefix="/api/v1/managerial")
app.include_router(staff_router,     prefix="/api/v1/managerial")
app.include_router(threshold_router, prefix="/api/v1/managerial")
app.include_router(dataset_router,   prefix="/api/v1/managerial")
app.include_router(auth_routes.router, prefix="/api/v1/managerial")

@app.get("/")
async def root():
    return {"message": "Managerial Service is running"}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host='0.0.0.0', port=8006, reload=True)
