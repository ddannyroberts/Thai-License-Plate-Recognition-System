from pydantic import BaseModel
from typing import Optional, Any
class PlateCreateResponse(BaseModel):
    id: int
    plate_text: str
    province_text: Optional[str] = None
    confidence: Optional[float] = None
    is_new_plate: Optional[bool] = True
    seen_count: Optional[int] = 1
    first_seen_at: Optional[str] = None  # ISO format timestamp
    first_seen_info: Optional[dict] = None  # Info about the first detection record
    duplicate_records: Optional[list] = None  # List of duplicate record IDs and info
    plate_image: Optional[str] = None  # Path to cropped plate image
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
