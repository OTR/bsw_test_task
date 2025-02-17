import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.di.container import init_container
from src.infra.api.v1.error_handlers import register_error_handlers, exception_handlers
from src.infra.api.v1.routes import router as event_router


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app: FastAPI = FastAPI(
        title="Line Provider API",
        description="API for managing betting events and lines",
        version="1.0.0",
        # Explicitly add exception handlers during app creation
        exception_handlers=exception_handlers
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, replace with specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize dependency injection container
    init_container()

    # Register API routes
    app.include_router(event_router, prefix="/api/v1")

    # Register error handlers
    register_error_handlers(app)

    return app


app: FastAPI = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)
