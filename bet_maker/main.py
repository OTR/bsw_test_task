import traceback

try:
    from contextlib import asynccontextmanager

    import uvicorn
    from fastapi import FastAPI

    from src.infra.api.v1.routes import router as bet_router
    from src.infra.api.v1.error_handler import register_exception_handlers
    from src.infra.repository.poll_events import lifespan_event_polling
    from src.infra.database import initialize_database, close_database_connection


    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await initialize_database()

        async with lifespan_event_polling():
            yield

        await close_database_connection()


    app = FastAPI(
        title="Bet Maker API",
        description="Сервис для рамещения ставок на события",
        version="1.0.0",
        lifespan=lifespan
    )

    register_exception_handlers(app)

    app.include_router(bet_router, prefix="/api/v1")

    if __name__ == "__main__":
        uvicorn.run("main:app", port=8081, reload=True)
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    traceback.print_exc()
    raise
