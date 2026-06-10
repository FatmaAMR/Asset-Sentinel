from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router as querying_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(querying_router)

@app.get("/")
def read_root():
    return {"message": "Querying Service is Running"}