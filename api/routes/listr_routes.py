from fastapi import APIRouter

router = APIRouter(prefix="/listr", tags=["listr"])

@router.get("/status")
async def listr_status():
    return {"module": "listr", "status": "ok"}
