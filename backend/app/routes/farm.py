from fastapi import APIRouter
from typing import List, Dict, Any
from app.database import query_db, query_one

router = APIRouter(prefix="/farms", tags=["Farm Management"])

@router.get("/")
async def get_farms():
    farms = query_db("SELECT * FROM farms")
    for f in farms:
        f["fields"] = query_db("SELECT crop_name as current_crop, area_acres, stage, health_status FROM crops WHERE farm_id = ?", (f["id"],))
    return farms

@router.get("/crops")
async def get_crops():
    return query_db("SELECT * FROM crops")
