from fastapi import APIRouter

router = APIRouter(tags=["watchr"])

@router.get("/status")
async def watchr_status():
    return {"module": "watchr", "status": "ok"}
