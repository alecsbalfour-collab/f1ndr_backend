from fastapi import APIRouter

router = APIRouter(
    prefix="/dealr",
    tags=["dealr"]
)

@router.get("/status")
async def dealr_status():
    return {"module": "dealr", "status": "ok"}
