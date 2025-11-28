from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, func
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    salt = Column(String(32), nullable=False)
    role = Column(String(20), nullable=False, default="user")  # user or admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

class PlateRecord(Base):
    __tablename__ = "plate_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)  # Reference to user who uploaded
    plate_text = Column(String(64), index=True)
    province_text = Column(String(64), nullable=True)
    confidence = Column(Float, nullable=True)
    image_path = Column(Text, nullable=True)  # Original uploaded image
    plate_image_path = Column(Text, nullable=True)  # Cropped plate image
    detections_json = Column(Text, nullable=True)
    is_new_plate = Column(Boolean, default=True)  # True if first time seeing this plate, False if duplicate
    seen_count = Column(Integer, default=1)  # Number of times this plate has been seen
    first_seen_at = Column(DateTime(timezone=True), nullable=True)  # First time this plate was detected
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
