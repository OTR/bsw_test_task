import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.di.container import init_container
from src.infra.api.v1.error_handlers import register_error_handlers, exception_handlers
from src.infra.api.v1.routes import router as event_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Line Provider API",
        description="Сервис для управления событиями для ставок",
        version="1.0.0",
        exception_handlers=exception_handlers
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    init_container()
    app.include_router(event_router, prefix="/api/v1")
    register_error_handlers(app)

    return app


app: FastAPI = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)
