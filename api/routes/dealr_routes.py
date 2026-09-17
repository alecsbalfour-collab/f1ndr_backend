from fastapi import APIRouter

router = APIRouter(tags=["dealr"])

@router.get("/status")
async def dealr_status():
    return {"module": "dealr", "status": "ok"}
