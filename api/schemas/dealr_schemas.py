from pydantic import BaseModel
from typing import Optional, List

class Dealr(BaseModel):
    id: str
    name: str
    city: Optional[str] = None
    province: Optional[str] = None
    phone: Optional[str] = None

class DealrSearchRequest(BaseModel):
    query: str

class DealrSearchResponse(BaseModel):
    results: List[Dealr]
