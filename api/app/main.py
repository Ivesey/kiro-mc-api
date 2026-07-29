from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import cases

app = FastAPI(title="MicroDigitech Support Cases API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases.router, prefix="/cases", tags=["cases"])


@app.get("/", summary="Health check", description="Returns API status")
def root():
    return {"status": "ok"}
