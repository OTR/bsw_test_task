import time

from fastapi import FastAPI

from src.routes import router as event_router

app = FastAPI()

app.include_router(event_router, prefix="/api/v1")
