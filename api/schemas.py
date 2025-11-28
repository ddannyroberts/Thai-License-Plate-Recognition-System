from pydantic import BaseModel
from typing import Optional, Any
class PlateCreateResponse(BaseModel):
    id: int
    plate_text: str
    province_text: Optional[str] = None
    confidence: Optional[float] = None
    is_new_plate: Optional[bool] = True
    seen_count: Optional[int] = 1
class PlateRecordOut(BaseModel):
    id: int
    plate_text: str
    province_text: Optional[str]
    confidence: Optional[float]
    created_at: Optional[str]
    image_path: Optional[str]
    class Config:
        from_attributes = True
class DetectResult(BaseModel):
    plate_text: str
    province_text: Optional[str]
    confidence: Optional[float]
    raw: Any
