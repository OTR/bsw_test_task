from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

router = APIRouter(tags=["Static files"])
templates = Jinja2Templates(directory="template")

@router.get(
    "/",
    response_class=HTMLResponse
)
async def get_index_page(request: Request):
    """"""
    return templates.TemplateResponse("index.html", {"request": request})

@router.get(
    "/events", 
    response_class=HTMLResponse
)
async def get_events(
    request: Request, 
    status: Optional[str] = Query(None, description="Вывести события по статусу")
):
    """"""
    if not status:
        status = "all"
        
    valid_statuses = ["all", "new", "finished_win", "finished_lose"]
    if status not in valid_statuses:
        status = "all"
    

    return templates.TemplateResponse(
        "events.html", 
        {"request": request, "status": status}
    )
