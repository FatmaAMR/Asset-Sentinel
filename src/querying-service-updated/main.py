from fastapi import FastAPI
from api.routes import router as querying_router


app = FastAPI()
app.include_router(querying_router)

@app.get("/")
def read_root():
    return {"message": "Querying Service is Running"}

