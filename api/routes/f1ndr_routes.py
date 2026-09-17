from fastapi import APIRouter

router = APIRouter(tags=["f1ndr"])

@router.get("/status")
async def f1ndr_status():
    return {"module": "f1ndr", "status": "ok"}
