from fastapi import APIRouter

router = APIRouter(tags=["listr"])

@router.get("/status")
async def listr_status():
    return {"module": "listr", "status": "ok"}
