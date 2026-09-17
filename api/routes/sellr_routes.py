from fastapi import APIRouter

router = APIRouter(tags=["sellr"])

@router.get("/status")
async def sellr_status():
    return {"module": "sellr", "status": "ok"}
