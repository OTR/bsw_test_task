from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Static files"])

@router.get("/")
async def get_index_page():
    with open("template/index.html") as f:
        return HTMLResponse(f.read())
