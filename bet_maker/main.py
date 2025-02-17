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
        """
        Manages the application lifecycle and its resources.
        
        This lifespan manager:
        1. Initializes and cleans up database connections
        2. Manages the event polling background task
        """
        # Initialize database when app starts
        await initialize_database()
        
        # Start event polling as a properly managed background task
        async with lifespan_event_polling():
            # Yield control back to FastAPI
            yield
        
        # Cleanup resources on app shutdown
        await close_database_connection()


    app = FastAPI(
        title="Bet Maker API",
        description="Service for placing and managing bets on events",
        version="1.0.0",
        lifespan=lifespan
    )

    # Register all exception handlers
    register_exception_handlers(app)

    # Include API routers
    app.include_router(bet_router, prefix="/api/v1")

    if __name__ == "__main__":
        uvicorn.run("main:app", port=8081, reload=True)
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    traceback.print_exc()
    raise
