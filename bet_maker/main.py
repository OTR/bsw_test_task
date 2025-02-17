from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI

from src.routes import router as bet_router
from src.services import poll_events


@asynccontextmanager
async def lifespan(app: FastAPI):
    """запустить опрос событий при старте приложения"""
    background_tasks = BackgroundTasks()
    background_tasks.add_task(poll_events)
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(bet_router, prefix="/api/v1")
