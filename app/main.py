from fastapi import FastAPI
from app.routers import cases

app = FastAPI(title="Case API", version="1.0.0")
app.include_router(cases.router, prefix="/cases", tags=["cases"])


@app.get("/", summary="Health check", description="Returns API status")
def root():
    return {"status": "ok"}
