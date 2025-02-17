from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn

from src.routes import router as static_router
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(static_router, prefix="")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
